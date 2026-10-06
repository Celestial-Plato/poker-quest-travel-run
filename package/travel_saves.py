"""Shared progress backups and manual restoration."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

def snapshot(profile, backup_root, label='manual'):
    profile = Path(profile)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%fZ')
    destination = Path(backup_root) / (timestamp + '-' + label)
    destination.mkdir(parents=True, exist_ok=False)
    files = {}
    for source in profile.glob('*.sol'):
        if not source.is_file() or source.is_symlink():
            raise RuntimeError('Unsupported save file: ' + source.name)
        shutil.copy2(source, destination / source.name)
        if source.read_bytes() != (destination / source.name).read_bytes():
            raise RuntimeError('Save backup verification failed: ' + source.name)
        files[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (destination / 'snapshot.json').write_text(json.dumps({'profile': str(profile), 'files': files}, indent=2), encoding='utf-8')
    (destination / '.complete').write_bytes(b'')
    return destination

def restore_snapshot(profile, backup, backup_root):
    profile, backup = Path(profile), Path(backup)
    if not (backup / '.complete').is_file():
        raise RuntimeError('The selected backup is incomplete.')
    saves = list(backup.glob('*.sol'))
    if not saves:
        raise RuntimeError('The selected backup contains no progress files.')
    for source in saves:
        if source.is_symlink() or not source.is_file():
            raise RuntimeError('Unsupported backup file: ' + source.name)
    manifest = backup / 'snapshot.json'
    if manifest.exists():
        expected = json.loads(manifest.read_text(encoding='utf-8'))['files']
        if set(expected) != {p.name for p in saves} or any(hashlib.sha256(p.read_bytes()).hexdigest() != expected[p.name] for p in saves):
            raise RuntimeError('The selected save backup is damaged.')
    recovery = snapshot(profile, backup_root, 'before-restore')
    profile.mkdir(parents=True, exist_ok=True)
    try:
        for source in saves:
            staged = profile / (source.name + '.tmp')
            shutil.copy2(source, staged)
            staged.replace(profile / source.name)
        for current in profile.glob('*.sol'):
            if current.name not in {p.name for p in saves}:
                current.unlink()
    except Exception:
        for current in profile.glob('*.sol'):
            if not (recovery / current.name).exists():
                current.unlink()
        for source in recovery.glob('*.sol'):
            shutil.copy2(source, profile / source.name)
        raise
    return recovery

