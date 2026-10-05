"""Player installer for the Workshop package. Never launches Poker Quest."""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys

import steam_paths
import travel_patch
from game_picker import choose_game,SelectionCancelled

PACKAGE=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
ORIGINAL_GAME_SHA256='edcc38527f3321c7324f9700a40d318ef178bc26c0563814835ffea603aa802b'
ORIGINAL_CSV_SHA256='7c02af7166de37d737b5253b86317de3b8daf00136b22be1a980c978dd7d0bba'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path,record):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temporary,path)

def inside(root,relative):
    result=(root/relative).resolve()
    if not result.is_relative_to(root.resolve()):raise RuntimeError('Package path escapes its content folder.')
    return result

def validate_package():
    manifest=json.loads((PACKAGE/'release-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('formatVersion')!=1:raise RuntimeError('Unsupported release manifest.')
    for entry in manifest['files']:
        path=inside(PACKAGE,entry['path'])
        if not path.is_file() or digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:
            raise RuntimeError('Package file is missing or changed: '+entry['path'])
    spec=json.loads((PACKAGE/'travel-patch.json').read_text(encoding='utf-8'))
    if spec['gameSha256']!=ORIGINAL_GAME_SHA256 or spec['version']!=manifest['version']:
        raise RuntimeError('Patch version differs from the release manifest.')
    return manifest,spec

def state_root():
    if not os.environ.get('LOCALAPPDATA'):raise RuntimeError('LOCALAPPDATA is unavailable.')
    return (Path(os.environ['LOCALAPPDATA'])/'Playsaurus/PokerQuestTravelRun').resolve()

def initialize_profile(game,root):
    profile=root/'appdata/Playsaurus/PokerQuest'
    marker=profile/'travel-profile.json'
    if marker.exists():return profile
    profile.mkdir(parents=True,exist_ok=True)
    normal=Path(os.environ['APPDATA'])/'Playsaurus/PokerQuest'
    source=normal
    record=game/travel_patch.INSTALL_RECORD
    if record.exists():
        previous=json.loads(record.read_text(encoding='utf-8'))
        # Migrate saves from a verified earlier Travel Run installation.
        if (previous.get('originalSha256')==ORIGINAL_GAME_SHA256
                and previous.get('installedSha256')==digest(game/'PokerQuest.exe')):
            old=Path(previous.get('profile',''))
            if old.is_dir() and (old/'travel-profile.json').exists():source=old
    for path in source.glob('*.sol'):
        destination=profile/path.name
        if not destination.exists():shutil.copy2(path,destination)
    for name in ('resolution.txt','last_version.txt'):
        destination=profile/name
        if (source/name).is_file() and not destination.exists():shutil.copy2(source/name,destination)
    atomic_json(marker,{'initializedAt':datetime.datetime.now().astimezone().isoformat(),
                       'copiedFrom':str(source),'savesAreSeparate':True})
    return profile

def prepare_data(game,profile,spec):
    original=game/'csv/WORLD_MODIFIERS.csv'
    if digest(original)!=ORIGINAL_CSV_SHA256:raise RuntimeError('The original modifier table differs from supported v63 data.')
    addon=(PACKAGE/'add/WORLD_MODIFIERS.csv').read_bytes()
    target=profile/'modded_csvs/csv/WORLD_MODIFIERS.csv'
    target.parent.mkdir(parents=True,exist_ok=True)
    # Match the official loader's append format without executing its game launcher.
    combined=original.read_bytes().rstrip(b'\r\n')+b'\n'+addon.lstrip(b'\r\n')
    text=combined.decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text)))
    if len({r['id'] for r in rows})!=len(rows):raise RuntimeError('Duplicate modifier IDs in merged data.')
    for name in ('TRAVEL BALANCED slow-foes','TRAVEL BALANCED sensitivity','TRAVEL Impostor'):
        if not any(r['internalName']==name for r in rows):raise RuntimeError('Travel modifier is missing: '+name)
    # Reproduce the official loader's complete local CSV overlay. These files
    # come from the player's installation, never from the Workshop package.
    for source in (game/'csv').glob('*.csv'):
        if source.name=='WORLD_MODIFIERS.csv':continue
        destination=target.parent/source.name
        staged=destination.with_suffix('.tmp')
        shutil.copy2(source,staged);os.replace(staged,destination)
    temporary=target.with_suffix('.tmp');temporary.write_bytes(combined);os.replace(temporary,target)
    (profile/'modded_imgs').mkdir(exist_ok=True)
    mods=profile/'mods';mods.mkdir(exist_ok=True)
    (mods/'mods.txt').write_text('TravelRun\n',encoding='utf-8')
    mod=mods/'TravelRun/add';mod.mkdir(parents=True,exist_ok=True)
    shutil.copy2(PACKAGE/'add/WORLD_MODIFIERS.csv',mod/'WORLD_MODIFIERS.csv')
    shutil.copy2(PACKAGE/'metadata.json',mods/'TravelRun/metadata.json')
    (profile/'is_modded.txt').write_text('1',encoding='ascii')
    atomic_json(profile/'travel-data-version.json',{'version':spec['version'],'csvSha256':digest(target)})

def cache_tools(root,manifest):
    cache=root/'installed-tools'
    cache.mkdir(parents=True,exist_ok=True)
    for entry in manifest['files']:
        source=inside(PACKAGE,entry['path']);destination=inside(cache,entry['path'])
        destination.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=destination.resolve():shutil.copy2(source,destination)
    if (PACKAGE/'release-manifest.json').resolve()!=(cache/'release-manifest.json').resolve():
        shutil.copy2(PACKAGE/'release-manifest.json',cache/'release-manifest.json')
    return cache

def install(game):
    manifest,spec=validate_package()
    original=travel_patch.original_executable(game,spec)
    if digest(game/'csv/WORLD_MODIFIERS.csv')!=ORIGINAL_CSV_SHA256:
        raise RuntimeError('Unsupported original modifier table.')
    target=game/'PokerQuest.exe';before=digest(target)
    root=state_root();root.mkdir(parents=True,exist_ok=True)
    profile=initialize_profile(game,root)
    prepare_data(game,profile,spec)
    build_dir=root/'cache';build_dir.mkdir(exist_ok=True)
    built=build_dir/'PokerQuest.patched.exe'
    report=travel_patch.patch_executable(game,built,profile,package=PACKAGE)
    backup=game/travel_patch.BACKUP_NAME
    if backup.exists():
        if digest(backup)!=ORIGINAL_GAME_SHA256:raise RuntimeError('Original-game backup differs; refusing to overwrite it.')
    else:shutil.copy2(original,backup)
    if digest(backup)!=ORIGINAL_GAME_SHA256:raise RuntimeError('Backup verification failed.')
    cache=cache_tools(root,manifest)
    if digest(target)!=before:raise RuntimeError('The game executable changed during preparation. Replacement was cancelled.')
    record=game/travel_patch.INSTALL_RECORD
    previous=record.read_bytes() if record.exists() else None
    atomic_json(record,{'version':spec['version'],'installedAt':datetime.datetime.now().astimezone().isoformat(),
                        'originalSha256':ORIGINAL_GAME_SHA256,'installedSha256':report['sha256'],
                        'backup':str(backup),'profile':str(profile),'package':str(cache),
                        'installer':str(cache/'InstallTravelRun.exe')})
    temporary=game/'PokerQuest.TravelRun.tmp'
    try:
        shutil.copy2(built,temporary)
        if digest(temporary)!=report['sha256']:raise RuntimeError('Replacement verification failed.')
        os.replace(temporary,target)
    except Exception:
        if temporary.exists():temporary.unlink()
        if previous is None:record.unlink()
        else:record.write_bytes(previous)
        raise
    atomic_json(root/'installation.json',{'gameDirectory':str(game),'version':spec['version'],'profile':str(profile)})
    print('Travel Run installed. Start Poker Quest from Steam, then choose New Run > Travel Run.')
    print('Separate saves: '+str(profile))
    print('Original executable backup: '+str(backup))
    print('Restore tool: '+str(cache/'RestoreOriginal.cmd'))

def restore(game):
    target=game/'PokerQuest.exe'
    if digest(target)==ORIGINAL_GAME_SHA256:
        print('The original game executable is already installed.');return
    record=game/travel_patch.INSTALL_RECORD
    if not record.is_file():raise RuntimeError('Travel Run installation record is missing.')
    info=json.loads(record.read_text(encoding='utf-8'))
    if digest(target)!=info.get('installedSha256'):raise RuntimeError('The game executable differs from the recorded Travel Run installation.')
    backup=game/travel_patch.BACKUP_NAME
    if not backup.is_file() or digest(backup)!=ORIGINAL_GAME_SHA256:raise RuntimeError('A verified original executable backup was not found.')
    temporary=game/'PokerQuest.restore.tmp'
    try:
        shutil.copy2(backup,temporary)
        if digest(temporary)!=ORIGINAL_GAME_SHA256:raise RuntimeError('Restore verification failed.')
        os.replace(temporary,target)
    finally:
        if temporary.exists():temporary.unlink()
    print('Original game executable restored. Original saves and mods were not changed.')
    print('Travel Run saves and backups were kept.')

def locate_game(explicit):
    if explicit:return steam_paths.find_game(explicit)
    try:return steam_paths.find_game()
    except (OSError,RuntimeError,ValueError) as error:
        print('Automatic game detection failed: '+str(error))
        print('Select PokerQuest.exe in the file picker, or cancel to exit without installing.')
        return steam_paths.find_game(choose_game())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir',type=Path,help='Override automatic Steam detection.')
    parser.add_argument('--restore',action='store_true')
    parser.add_argument('--check',action='store_true',help='Check package files and locate the game without installing.')
    parser.add_argument('--no-pause',action='store_true')
    args=parser.parse_args()
    code=0
    try:
        if os.name!='nt':raise RuntimeError('This package supports Windows x64 only.')
        game=locate_game(args.game_dir)
        print('Poker Quest folder: '+str(game))
        if args.check:
            manifest,spec=validate_package();travel_patch.original_executable(game,spec)
            print('Package and game version checks passed: '+manifest['version'])
        elif args.restore:restore(game)
        else:install(game)
    except SelectionCancelled:
        print('Game selection cancelled. Nothing was installed or restored.')
    except Exception as error:
        print('Unable to complete: '+str(error),file=sys.stderr)
        print('Close Poker Quest before installing or restoring. If Steam detection fails, use --game-dir.',file=sys.stderr)
        code=1
    if not args.no_pause:
        try:input('Press Enter to close...')
        except EOFError:pass
    return code

if __name__=='__main__':sys.exit(main())
