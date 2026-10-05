"""Build only our version-locked payload. Does not run or alter the game."""
import hashlib
import json
from pathlib import Path
import subprocess

import pefile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = ROOT / 'build/native'
PACKAGE = ROOT / 'package'

def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    subprocess.run(['cl', '/nologo', '/O2', '/GS-', '/GR-', '/LD', '/Zl',
                    str(HERE / 'travel_hooks.c'), '/Fo' + str(BUILD / 'travel_hooks.obj'),
                    '/link', '/NOENTRY', '/NODEFAULTLIB', '/FIXED', '/DYNAMICBASE:NO',
                    '/OUT:' + str(BUILD / 'travel_hooks.dll'),
                    '/IMPLIB:' + str(BUILD / 'travel_hooks.lib')], check=True)
    dll = pefile.PE(str(BUILD / 'travel_hooks.dll'))
    if hasattr(dll, 'DIRECTORY_ENTRY_IMPORT') or hasattr(dll, 'DIRECTORY_ENTRY_BASERELOC'):
        raise RuntimeError('Payload must have no imports or relocations.')
    payload = bytearray(dll.OPTIONAL_HEADER.SizeOfImage)
    for section in dll.sections:
        payload[section.VirtualAddress:section.VirtualAddress + section.SizeOfRawData] = section.get_data()
    spec = json.loads((PACKAGE / 'travel-patch.json').read_text(encoding='utf-8'))
    spec['exports'] = {symbol.name.decode(): symbol.address for symbol in dll.DIRECTORY_ENTRY_EXPORT.symbols}
    for patch in spec['patches']:
        if patch['function'] not in spec['exports']:
            raise RuntimeError('Missing hook export: ' + patch['function'])
    spec['runtimeFunctions'] = [[entry.struct.BeginAddress, entry.struct.EndAddress, entry.struct.UnwindData]
                               for entry in dll.DIRECTORY_ENTRY_EXCEPTION]
    spec['payloadSha256'] = hashlib.sha256(payload).hexdigest()
    (PACKAGE / 'travel-code.bin').write_bytes(payload)
    (PACKAGE / 'travel-patch.json').write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')
    print('Built native payload:', len(payload), 'bytes. No game files accessed.')

if __name__ == '__main__':
    main()
