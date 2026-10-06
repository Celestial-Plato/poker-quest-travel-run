"""Build one installer and either/both complete distribution channels."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'package'
FILES = ('add/WORLD_MODIFIERS.csv', 'EFFECTS.md', 'game_picker.py', 'install_travel_run.py',
         'InstallTravelRun.cmd', 'metadata.json', 'README.en.md', 'README.zh-CN.md',
         'RestoreOriginal.cmd', 'runtime-licenses.txt', 'steam_paths.py', 'travel-code.bin',
         'travel-patch.json', 'travel_patch.py')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', choices=('all', 'github', 'workshop'), default='all')
    args = parser.parse_args()
    spec = json.loads((PACKAGE / 'travel-patch.json').read_text(encoding='utf-8'))
    if hashlib.sha256((PACKAGE / 'travel-code.bin').read_bytes()).hexdigest() != spec['payloadSha256']:
        raise RuntimeError('Native payload differs from patch metadata.')
    build = ROOT / 'build'
    dist = ROOT / 'dist'
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--console',
                    '--name', 'InstallTravelRun', '--paths', str(PACKAGE), '--distpath', str(build / 'exe'),
                    '--workpath', str(build / 'pyinstaller'), '--specpath', str(build),
                    str(PACKAGE / 'install_travel_run.py')], check=True)
    channels = ('github', 'workshop') if args.channel == 'all' else (args.channel,)
    for channel in channels:
        stage = dist / ('TravelRun-Installer' if channel == 'github' else 'TravelRun-Workshop/content/TravelRun')
        stage.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            source = PACKAGE / name
            if channel == 'workshop' and name in ('README.zh-CN.md', 'README.en.md'):
                source = ROOT / 'distribution/workshop' / name
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copy2(build / 'exe/InstallTravelRun.exe', stage / 'InstallTravelRun.exe')
        names = sorted((*FILES, 'InstallTravelRun.exe'))
        manifest = {'formatVersion': 1, 'version': spec['version'], 'gameVersion': 63, 'build': 2021,
                    'activeChoices': 22, 'hiddenLegacyDefinitions': 56, 'distribution': channel + '-installer',
                    'files': [{'path': name, 'bytes': (stage / name).stat().st_size,
                               'sha256': hashlib.sha256((stage / name).read_bytes()).hexdigest()} for name in names]}
        (stage / 'release-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        prefix = 'TravelRun-Installer' if channel == 'github' else 'TravelRun-Workshop/content/TravelRun'
        archive = dist / (('TravelRun-Installer-v' if channel == 'github' else 'TravelRun-Workshop-v') + spec['version'] + '.zip')
        with zipfile.ZipFile(archive, 'w') as stream:
            for name in (*names, 'release-manifest.json'):
                entry = zipfile.ZipInfo(prefix + '/' + name, (2026, 10, 6, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                stream.writestr(entry, (stage / name).read_bytes())
        checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
        archive.with_suffix('.zip.sha256').write_text(checksum + '  ' + archive.name + '\n', encoding='ascii')
        print('Release:', archive, '\nSHA256:', checksum)
    print('Installer compiled once for the selected channels. Installer and game were not executed.')

if __name__ == '__main__':
    main()
