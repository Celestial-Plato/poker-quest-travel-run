"""Locate installed Poker Quest using Steam's registry and library manifests."""
import os
from pathlib import Path
import re

APP_ID='1184820'

def vdf_value(text,key):
    match=re.search(r'"'+re.escape(key)+r'"\s*"((?:\\.|[^"\\])*)"',text,re.I)
    if not match:return None
    return match.group(1).replace('\\\\','\\').replace('\\"','"')

def steam_roots():
    roots=[]
    if os.name=='nt':
        import winreg
        for hive,key,value in (
            (winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam','SteamPath'),
            (winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam','InstallPath'),
            (winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Valve\Steam','InstallPath')):
            try:
                with winreg.OpenKey(hive,key) as handle:
                    roots.append(Path(winreg.QueryValueEx(handle,value)[0]))
            except OSError:pass
    for name in ('ProgramFiles(x86)','ProgramFiles'):
        if os.environ.get(name):roots.append(Path(os.environ[name])/'Steam')
    return list(dict.fromkeys(path.resolve() for path in roots if path.is_dir()))

def game_candidates():
    libraries=[]
    for root in steam_roots():
        libraries.append(root)
        file=root/'steamapps/libraryfolders.vdf'
        if not file.exists():continue
        text=file.read_text(encoding='utf-8-sig')
        values=re.findall(r'"path"\s*"((?:\\.|[^"\\])*)"',text,re.I)
        # Older Steam clients stored the library path directly under a numeric key.
        values+=re.findall(r'"\d+"\s*"((?:\\.|[^"\\])*)"',text)
        libraries.extend(Path(v.replace('\\\\','\\').replace('\\"','"')) for v in values)
    games=[]
    for library in dict.fromkeys(libraries):
        manifest=library/f'steamapps/appmanifest_{APP_ID}.acf'
        if not manifest.is_file():continue
        folder=vdf_value(manifest.read_text(encoding='utf-8-sig'),'installdir')
        if not folder or Path(folder).is_absolute() or '..' in Path(folder).parts:continue
        common=(library/'steamapps/common').resolve()
        game=(common/folder).resolve()
        if game.is_relative_to(common) and (game/'PokerQuest.exe').is_file():games.append(game)
    return list(dict.fromkeys(games))

def find_game(explicit=None):
    if explicit:
        game=Path(explicit).expanduser().resolve(strict=True)
        if not (game/'PokerQuest.exe').is_file():raise RuntimeError('PokerQuest.exe was not found in the selected folder.')
        return game
    games=game_candidates()
    if len(games)==1:return games[0]
    if not games:raise RuntimeError('Poker Quest was not found through Steam. Specify --game-dir followed by the game folder.')
    raise RuntimeError('Multiple Poker Quest installations were found. Specify --game-dir to select one: '+', '.join(map(str,games)))
