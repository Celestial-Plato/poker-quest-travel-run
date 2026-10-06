"""Version-checked native patch builder. Writes only the requested output copy."""
import hashlib,json,os,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
BACKUP_NAME='PokerQuest.before-TravelRun.exe'
INSTALL_RECORD='travel-run-install.json'
def original_executable(game,spec):
    installed=game/'PokerQuest.exe';current=hashlib.sha256(installed.read_bytes()).hexdigest()
    if current==spec['gameSha256']:return installed
    record=game/INSTALL_RECORD;backup=game/BACKUP_NAME
    if record.is_file() and backup.is_file():
        info=json.loads(record.read_text(encoding='utf-8'))
        if current==info.get('installedSha256') and hashlib.sha256(backup.read_bytes()).hexdigest()==spec['gameSha256']:
            return backup
    raise RuntimeError('Travel Run supports Poker Quest v63 / build 2021 only. Installed executable differs.')
def align(n,a):return (n+a-1)//a*a
class PE:
    def __init__(self,data):
        self.data=data;self.nt=struct.unpack_from('<I',data,0x3c)[0]
        if data[self.nt:self.nt+4]!=b'PE\0\0' or struct.unpack_from('<H',data,self.nt+4)[0]!=0x8664:raise RuntimeError('Expected a Windows x64 executable')
        self.count=struct.unpack_from('<H',data,self.nt+6)[0];self.optional=self.nt+24
        self.table=self.optional+struct.unpack_from('<H',data,self.nt+20)[0]
        self.sections=[struct.unpack_from('<8sIIII',data,self.table+i*40) for i in range(self.count)]
    def raw(self,rva):
        for name,vs,va,rs,rp in self.sections:
            if va<=rva<va+max(vs,rs):return rp+rva-va
        raise ValueError('Unmapped RVA')
def patch_executable(game,output,profile,package=HERE):
    spec=json.loads((package/'travel-patch.json').read_text());original=original_executable(game,spec).read_bytes()
    installed_hash=hashlib.sha256((game/'PokerQuest.exe').read_bytes()).hexdigest()
    body=bytearray((package/'travel-code.bin').read_bytes())
    if hashlib.sha256(body).hexdigest()!=spec['payloadSha256']:raise RuntimeError('Travel Run code payload is damaged')
    data=bytearray(original);pe=PE(data)
    sa,fa=struct.unpack_from('<II',data,pe.optional+32);slot=pe.table+pe.count*40
    if slot+40>struct.unpack_from('<I',data,pe.optional+60)[0] or any(data[slot:slot+40]):raise RuntimeError('No spare executable section header')
    va=align(max(va+max(vs,rs) for _,vs,va,rs,rp in pe.sections),sa)
    runtime_rva,runtime_size=struct.unpack_from('<II',data,pe.optional+112+24)
    runtime=[struct.unpack_from('<III',data,pe.raw(runtime_rva)+i) for i in range(0,runtime_size,12)]
    runtime.extend((va+a,va+b,va+c) for a,b,c in spec['runtimeFunctions'])
    def append(blob,a=16):
        offset=align(len(body),a);body.extend(b'\0'*(offset-len(body)));body.extend(blob);return va+offset
    def branch(op,source,target):return op+struct.pack('<i',target-source-5)
    for patch in spec['patches']:
        site=patch['rva'];expected=bytes.fromhex(patch['expected']);raw=pe.raw(site)
        if data[raw:raw+len(expected)]!=expected:raise RuntimeError('Unexpected code at '+hex(site))
        target=va+spec['exports'][patch['function']]
        if patch['kind']=='call':replacement=branch(b'\xe8',site,target)
        else:
            thunk_rva=va+align(len(body),16)
            # RSI is the constructor's screen; its original GC stack is at RSP+0x30.
            thunk=bytearray.fromhex('48 83 ec 20 48 89 f1 48 8b 54 24 50')
            thunk.extend(branch(b'\xe8',thunk_rva+len(thunk),target))
            thunk.extend(bytes.fromhex('48 83 c4 20'));thunk.extend(expected)
            thunk.extend(branch(b'\xe9',thunk_rva+len(thunk),site+len(expected)))
            assert append(thunk)==thunk_rva
            unwind=append(bytes.fromhex('01 04 01 00 04 32 00 00'),4)
            runtime.append((thunk_rva,thunk_rva+len(thunk),unwind))
            replacement=branch(b'\xe9',site,thunk_rva)+b'\x90'*(len(expected)-5)
        data[raw:raw+len(expected)]=replacement
    for patch in spec.get('staticPatches',[]):
        raw=pe.raw(patch['rva']);expected=bytes.fromhex(patch['expected']);replacement=bytes.fromhex(patch['replacement'])
        if len(expected)!=len(replacement) or data[raw:raw+len(expected)]!=expected:raise RuntimeError('Unexpected code for '+patch['purpose'])
        data[raw:raw+len(expected)]=replacement
    # Keep App.getSaveDir and every caller original: progress, CSV/image mods,
    # settings and the external Mod Manager all use the normal shared profile.
    runtime.sort();pdata=append(b''.join(struct.pack('<III',*row) for row in runtime),4)
    rp=align(len(data),fa);rs=align(len(body),fa)
    data.extend(b'\0'*(rp-len(data)));data.extend(body);data.extend(b'\0'*(rs-len(body)))
    struct.pack_into('<8sIIIIIIHHI',data,slot,b'.travel\0',len(body),va,rs,rp,0,0,0,0,0xe0000020)
    struct.pack_into('<H',data,pe.nt+6,pe.count+1)
    struct.pack_into('<I',data,pe.optional+56,align(va+len(body),sa))
    struct.pack_into('<I',data,pe.optional+64,0)
    struct.pack_into('<II',data,pe.optional+112+24,pdata,len(runtime)*12)
    struct.pack_into('<II',data,pe.optional+112+32,0,0)
    if output.resolve()==(game/'PokerQuest.exe').resolve():raise RuntimeError('Refusing to overwrite the installed game')
    output.parent.mkdir(parents=True,exist_ok=True)
    if not output.exists() or hashlib.sha256(output.read_bytes()).digest()!=hashlib.sha256(data).digest():
        temporary=output.with_suffix('.tmp')
        try:
            temporary.write_bytes(data);os.replace(temporary,output)
        finally:
            if temporary.exists():temporary.unlink()
    assert hashlib.sha256((game/'PokerQuest.exe').read_bytes()).hexdigest()==installed_hash
    return {'payloadRva':va,'exports':{k:va+v for k,v in spec['exports'].items()},'copy':str(output),'sha256':hashlib.sha256(data).hexdigest(),'sharedProgress':True,'sharedMods':True}
