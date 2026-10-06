"""Register Travel's data with the original Mod Manager, preserving other mods.

The game's native overlay and Mod Manager must read the same profile. Install
updates only our modifier rows; manager Apply subsequently uses the ordinary
add/replace pipeline and user-selected mod order.
"""
import csv
import datetime
import io
import json
import os
from pathlib import Path
import shutil

WORKSHOP_ID = '3814137517'

def read_rows(data):
    return list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_suffix(path.suffix + '.tmp')
    staged.write_bytes(data)
    os.replace(staged, path)

def is_travel_mod(name, mods):
    if name.lower() == 'travelrun' or name == WORKSHOP_ID:
        return True
    path = mods / name / 'metadata.json'
    if path.is_file():
        try:
            return str(json.loads(path.read_text(encoding='utf-8-sig')).get('id')) == WORKSHOP_ID
        except (ValueError, OSError):
            pass
    return False

def prepare_shared_mods(game, normal, addon_path, metadata_path, backup_root):
    """No game/manager execution; no save writes. All conflicts checked first."""
    game, normal = Path(game), Path(normal)
    mods = normal / 'mods'
    enabled = mods / 'mods.txt'
    names = enabled.read_text(encoding='utf-8-sig').splitlines() if enabled.exists() else []
    names = [name.strip() for name in names if name.strip()]
    aliases = [name for name in names if is_travel_mod(name, mods)]
    # Reuse an existing Workshop registration so the manager displays one entry.
    canonical = aliases[0] if aliases else WORKSHOP_ID if (mods / WORKSHOP_ID).is_dir() else 'TravelRun'
    if Path(canonical).name != canonical or canonical in ('.', '..'):
        raise RuntimeError('Unsupported Travel mod directory name.')
    selected = [name for name in names if not is_travel_mod(name, mods)]
    selected.append(canonical)
    addon = addon_path.read_bytes()
    original = read_rows((game / 'csv/WORLD_MODIFIERS.csv').read_bytes())
    fields = original[0]
    id_index, name_index = fields.index('id'), fields.index('internalName')
    own_rows = [r for r in read_rows(addon) if r]
    own = {r[id_index]: r[name_index] for r in own_rows}
    if len(own) != len(own_rows) or any(not name.startswith('TRAVEL ') for name in own.values()):
        raise RuntimeError('Invalid Travel modifier definitions.')
    target = normal / 'modded_csvs/csv/WORLD_MODIFIERS.csv'
    # A disabled overlay may still exist after unloading mods. Respect the flag.
    active = (normal / 'is_modded.txt').is_file()
    rows = read_rows(target.read_bytes()) if active and target.exists() else original
    if not rows or rows[0] != fields:
        raise RuntimeError('Applied modifier schema differs from the supported game.')
    merged = [fields]
    seen = set()
    for row in rows[1:]:
        if not row:
            continue
        if len(row) != len(fields):
            raise RuntimeError('Applied modifier row has an invalid number of fields.')
        key = row[id_index]
        if key in own:
            if row[name_index] != own[key]:
                raise RuntimeError('Another mod uses Travel modifier ID ' + key)
            continue
        if key in seen:
            raise RuntimeError('Duplicate modifier ID in other mods: ' + key)
        seen.add(key)
        merged.append(row)
    merged.extend(own_rows)
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='\n').writerows(merged)
    metadata = json.loads(metadata_path.read_text(encoding='utf-8-sig'))
    metadata.update(id=int(WORKSHOP_ID), name='Travel Run',
                    description='Travel Run starting bonuses. Keep enabled when using the Travel Run program patch.')
    destinations = {
        target: stream.getvalue().encode('utf-8'),
        enabled: ('\n'.join(selected) + '\n').encode('utf-8'),
        mods / canonical / 'add/WORLD_MODIFIERS.csv': addon,
        mods / canonical / 'metadata.json': (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
        normal / 'is_modded.txt': str(len(selected)).encode('ascii'),
    }
    changed = {p: data for p, data in destinations.items() if not p.exists() or p.read_bytes() != data}
    backup = Path(backup_root) / ('shared-mods-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    if changed:
        backup.mkdir(parents=True, exist_ok=False)
        existed = {}
        for path in changed:
            existed[path] = path.read_bytes() if path.exists() else None
            if path.exists():
                copy = backup / path.relative_to(normal)
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, copy)
        try:
            for path, data in changed.items():
                atomic_write(path, data)
        except Exception:
            for path, data in existed.items():
                if data is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, data)
            raise
    return {'normalProfile': str(normal), 'travelMod': canonical,
            'enabledMods': selected, 'backup': str(backup) if changed else None,
            'otherModTablesChanged': False, 'saveFilesChanged': False}
