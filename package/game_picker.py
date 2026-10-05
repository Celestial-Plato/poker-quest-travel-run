"""Windows file picker used when automatic game discovery is unavailable."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path


class SelectionCancelled(Exception):
    pass


class OpenFileName(c.Structure):
    _fields_=[('lStructSize',w.DWORD),('hwndOwner',w.HWND),('hInstance',w.HINSTANCE),
              ('lpstrFilter',w.LPCWSTR),('lpstrCustomFilter',w.LPWSTR),
              ('nMaxCustFilter',w.DWORD),('nFilterIndex',w.DWORD),
              ('lpstrFile',w.LPWSTR),('nMaxFile',w.DWORD),
              ('lpstrFileTitle',w.LPWSTR),('nMaxFileTitle',w.DWORD),
              ('lpstrInitialDir',w.LPCWSTR),('lpstrTitle',w.LPCWSTR),
              ('Flags',w.DWORD),('nFileOffset',w.WORD),('nFileExtension',w.WORD),
              ('lpstrDefExt',w.LPCWSTR),('lCustData',c.c_ssize_t),
              ('lpfnHook',c.c_void_p),('lpTemplateName',w.LPCWSTR),
              ('pvReserved',c.c_void_p),('dwReserved',w.DWORD),('FlagsEx',w.DWORD)]


def choose_game():
    """Return the folder of the chosen game; cancelling does not install anything."""
    dialog=c.WinDLL('comdlg32',use_last_error=True)
    kernel=c.WinDLL('kernel32',use_last_error=True)
    user=c.WinDLL('user32',use_last_error=True)
    kernel.GetConsoleWindow.argtypes=[];kernel.GetConsoleWindow.restype=w.HWND
    dialog.GetOpenFileNameW.argtypes=[c.POINTER(OpenFileName)]
    dialog.GetOpenFileNameW.restype=w.BOOL
    dialog.CommDlgExtendedError.argtypes=[];dialog.CommDlgExtendedError.restype=w.DWORD
    user.MessageBoxW.argtypes=[w.HWND,w.LPCWSTR,w.LPCWSTR,w.UINT]
    user.MessageBoxW.restype=c.c_int
    owner=kernel.GetConsoleWindow()
    filename=c.create_unicode_buffer(32768)
    options=OpenFileName()
    options.lStructSize=c.sizeof(options);options.hwndOwner=owner
    options.lpstrFilter='Poker Quest (PokerQuest.exe)\0PokerQuest.exe\0\0'
    options.nFilterIndex=1
    options.lpstrFile=c.cast(filename,w.LPWSTR);options.nMaxFile=len(filename)
    options.lpstrTitle='TRAVEL RUN - 请选择 / Select PokerQuest.exe'
    # Explorer UI, existing file/path, preserve CWD, no recent-document entry.
    options.Flags=0x00080000|0x00001000|0x00000800|0x00000008|0x02000000
    while True:
        if not dialog.GetOpenFileNameW(c.byref(options)):
            error=dialog.CommDlgExtendedError()
            if error:raise RuntimeError('Windows file picker failed (code '+hex(error)+'). Use --game-dir instead.')
            raise SelectionCancelled()
        selected=Path(filename.value).resolve()
        if selected.name.lower()=='pokerquest.exe' and selected.is_file():return selected.parent
        user.MessageBoxW(owner,'请选择游戏目录中的 PokerQuest.exe。\nPlease select PokerQuest.exe in the game folder.',
                         'TRAVEL RUN',0x10)
        filename.value=''
