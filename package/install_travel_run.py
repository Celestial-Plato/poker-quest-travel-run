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
import subprocess

import steam_paths
import travel_patch
from game_picker import choose_game,SelectionCancelled
from travel_mods import prepare_shared_mods
from travel_saves import snapshot,restore_snapshot

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

def ensure_game_closed():
    result=subprocess.run(['tasklist','/FI','IMAGENAME eq PokerQuest.exe','/FO','CSV','/NH'],capture_output=True,text=True,errors='replace',check=True)
    if any(row and row[0].lower()=='pokerquest.exe' for row in csv.reader(result.stdout.splitlines())):
        raise RuntimeError('Close Poker Quest before changing the installation or restoring saves.')

def initialize_profile(game,root):
    profile=Path(os.environ['APPDATA'])/'Playsaurus/PokerQuest'
    record=game/travel_patch.INSTALL_RECORD
    if record.exists():
        previous=json.loads(record.read_text(encoding='utf-8'))
        if (previous.get('originalSha256')==ORIGINAL_GAME_SHA256
                and previous.get('installedSha256')==digest(game/'PokerQuest.exe')):
            old=Path(previous.get('profile',''))
            if old.resolve()!=profile.resolve() and old.is_dir() and (old/'travel-profile.json').exists():
                backup=snapshot(old,root/'backups','legacy-travel')
                atomic_json(root/'legacy-progress-backup.json',{'profile':str(old),'backup':str(backup)})
    profile.mkdir(parents=True,exist_ok=True)
    return profile

def prepare_data(game,profile,spec,root=None):
    original=game/'csv/WORLD_MODIFIERS.csv'
    if digest(original)!=ORIGINAL_CSV_SHA256:raise RuntimeError('The original modifier table differs from supported v63 data.')
    report=prepare_shared_mods(game,profile,PACKAGE/'add/WORLD_MODIFIERS.csv',PACKAGE/'metadata.json',
                               (root or state_root())/'backups')
    atomic_json((root or state_root())/'shared-mods.json',report)
    return report

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
    ensure_game_closed()
    manifest,spec=validate_package()
    original=travel_patch.original_executable(game,spec)
    if digest(game/'csv/WORLD_MODIFIERS.csv')!=ORIGINAL_CSV_SHA256:
        raise RuntimeError('Unsupported original modifier table.')
    target=game/'PokerQuest.exe';before=digest(target)
    root=state_root();root.mkdir(parents=True,exist_ok=True)
    profile=initialize_profile(game,root)
    snapshot(profile,root/'backups','before-install')
    prepare_data(game,profile,spec,root)
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
                        'installer':str(cache/'InstallTravelRun.exe'),'sharedProgress':True,'sharedMods':True})
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
    print('Shared saves and Mod Manager data: '+str(profile))
    print('Travel Run automatically backs up progress before opening: '+str(profile/'TravelRun-backups'))
    print('Original executable backup: '+str(backup))
    print('Restore tool: '+str(cache/'RestoreOriginal.cmd'))

def restore(game):
    ensure_game_closed()
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
    print('Shared progress, other mods and all backups were kept.')

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
    parser.add_argument('--restore-saves',type=Path,help='Restore one complete progress snapshot, after backing up current progress.')
    parser.add_argument('--no-pause',action='store_true')
    args=parser.parse_args()
    code=0
    try:
        if os.name!='nt':raise RuntimeError('This package supports Windows x64 only.')
        if args.restore_saves:
            ensure_game_closed()
            normal=Path(os.environ['APPDATA'])/'Playsaurus/PokerQuest'
            root=state_root()
            recovery=restore_snapshot(normal,args.restore_saves,root/'backups')
            print('Progress restored. Current progress was backed up to: '+str(recovery))
            return 0
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
