import sys
import os
import getch as gh

if os.name == 'nt':
    import msvcrt
    import ctypes

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int),
                    ("visible", ctypes.c_byte)]

def hide_cursor():
    if os.name == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

def show_cursor():
    if os.name == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

def print_there(x, y, text):
     sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
     sys.stdout.flush()

def get_key():
    first_char = gh.getch()
    if first_char == '\x1b':
        try:
            ret = {'[2':'insert','[3':'delete', '[H':'home','[F':'end', '[5':'pgup','[6':'pgdown','[A': 'up', '[B': 'down', '[C': 'right', '[D': 'left'}[gh.getch() + gh.getch()]
        except:
            ret = 'NA'
        return ret
    else:
        return first_char



