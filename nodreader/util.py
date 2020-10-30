import sys
import os
import curses as cur

import sys

if os.name == 'nt':
    import ctypes
    from ctypes import POINTER, WinDLL, Structure, sizeof, byref
    from ctypes.wintypes import BOOL, SHORT, WCHAR, UINT, ULONG, DWORD, HANDLE

    import subprocess
    import msvcrt
    import winsound

    from ctypes import wintypes

def fix_borders():
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    hWnd = kernel32.GetConsoleWindow()
    win32gui.SetWindowLong(hWnd, win32con.GWL_STYLE, 
            win32gui.GetWindowLong(hWnd, win32com.GWL_STYLE) & win32con.WS_MAXIMIZEBOX & win32con.WS_SIZEBOX)


def maximize_console(lines=None):
    if os.name == "nt":
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        hWnd = kernel32.GetConsoleWindow()
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.ShowWindow(hWnd, 1)
        subprocess.check_call('mode.com con cols=124 lines=29')

    #kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    #user32 = ctypes.WinDLL('user32', use_last_error=True)

    #SW_MAXIMIZE = 3

    #kernel32.GetConsoleWindow.restype = wintypes.HWND
    #kernel32.GetLargestConsoleWindowSize.restype = wintypes._COORD
    #kernel32.GetLargestConsoleWindowSize.argtypes = (wintypes.HANDLE,)
    #user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
    #fd = os.open('CONOUT$', os.O_RDWR)
    #try:
    #    hCon = msvcrt.get_osfhandle(fd)
    #    max_size = kernel32.GetLargestConsoleWindowSize(hCon)
    #    if max_size.X == 0 and max_size.Y == 0:
    #        raise ctypes.WinError(ctypes.get_last_error())
    #finally:
    #    os.close(fd)
    #cols = max_size.X
    #hWnd = kernel32.GetConsoleWindow()
    #if cols and hWnd:
    #    if lines is None:
    #        lines = max_size.Y
    #    else:
    #        lines = max(min(lines, 9999), max_size.Y)

def resize_font_on_windows(height, get_size = False):
    LF_FACESIZE = 32
    STD_OUTPUT_HANDLE = -11

    class COORD(Structure):
        _fields_ = [
            ("X", SHORT),
            ("Y", SHORT),
        ]


    class CONSOLE_FONT_INFOEX(Structure):
        _fields_ = [
            ("cbSize", ULONG),
            ("nFont", DWORD),
            ("dwFontSize", COORD),
            ("FontFamily", UINT),
            ("FontWeight", UINT),
            ("FaceName", WCHAR * LF_FACESIZE)
        ]


    kernel32_dll = WinDLL("kernel32.dll")

    get_last_error_func = kernel32_dll.GetLastError
    get_last_error_func.argtypes = []
    get_last_error_func.restype = DWORD

    get_std_handle_func = kernel32_dll.GetStdHandle
    get_std_handle_func.argtypes = [DWORD]
    get_std_handle_func.restype = HANDLE

    get_current_console_font_ex_func = kernel32_dll.GetCurrentConsoleFontEx
    get_current_console_font_ex_func.argtypes = [HANDLE, BOOL, POINTER(CONSOLE_FONT_INFOEX)]
    get_current_console_font_ex_func.restype = BOOL

    set_current_console_font_ex_func = kernel32_dll.SetCurrentConsoleFontEx
    set_current_console_font_ex_func.argtypes = [HANDLE, BOOL, POINTER(CONSOLE_FONT_INFOEX)]
    set_current_console_font_ex_func.restype = BOOL

    # Get stdout handle
    stdout = get_std_handle_func(STD_OUTPUT_HANDLE)
    if not stdout:
        return ("{:s} error: {:d}".format(get_std_handle_func.__name__, get_last_error_func()))
    # Get current font characteristics
    font = CONSOLE_FONT_INFOEX()
    font.cbSize = sizeof(CONSOLE_FONT_INFOEX)
    res = get_current_console_font_ex_func(stdout, False, byref(font))
    if not res:
        return ("{:s} error: {:d}".format(get_current_console_font_ex_func.__name__, get_last_error_func()))
    # Display font information
    for field_name, _ in font._fields_:
        field_data = getattr(font, field_name)
        if field_name == "dwFontSize" and get_size:
            return field_data.Y
    # Alter font height
    font.dwFontSize.X = 10  # Changing X has no effect (at least on my machine)
    font.dwFontSize.Y = height
    # Apply changes
    res = set_current_console_font_ex_func(stdout, False, byref(font))
    if not res:
        return("{:s} error: {:d}".format(set_current_console_font_ex_func.__name__, get_last_error_func()))
    # Get current font characteristics again and display font size
    res = get_current_console_font_ex_func(stdout, False, byref(font))
    if not res:
        return("{:s} error: {:d}".format(get_current_console_font_ex_func.__name__, get_last_error_func()))
    return ""

if os.name == 'nt':
    import msvcrt

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int),
                    ("visible", ctypes.c_byte)]

def hide_cursor(useCur = True):
    if useCur:
        cur.curs_set(0)
    elif os.name == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

def show_cursor(useCur = True):
    if useCur:
        cur.curs_set(1)
    elif os.name == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

def mprint(text, stdscr =None, color=0, attr = None, end="\n", refresh = False):
    if stdscr is None:
        print(text, end=end)
    else:
        c = cur.color_pair(color)
        if attr is not None:
            c = cur.color_pair(color) | attr
        height, width = stdscr.getmaxyx()
        #stdscr.addnstr(text + end, height*width-1, c)
        stdscr.addstr(text + end, c)
        if not refresh:
            pass #stdscr.refresh(0,0, 0,0, height -5, width)
        else:
            #stdscr.refresh()
            pass

def print_there(x, y, text, stdscr = None, color=0, attr = None, pad = False):
    if stdscr is not None:
        c = cur.color_pair(color)
        if attr is not None:
            c = cur.color_pair(color) | attr
        height, width = stdscr.getmaxyx()
        #stdscr.addnstr(x, y, text, height*width-1, c)
        _len = (height*width)-x
        stdscr.addstr(x, y, text[:_len], c)
        if pad:
            pass #stdscr.refresh(0,0, x,y, height -5, width)
        else:
            pass # stdscr.refresh()
    else:
        sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
        sys.stdout.flush()
def clear_screen(stdscr = None):
    if stdscr is not None:
        stdscr.erase()
        stdscr.refresh()
    else:
        os.system('clear')
def rinput(stdscr, r, c, prompt_string, default=""):
    show_cursor()
    cur.echo() 
    stdscr.addstr(r, c, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(r, len(prompt_string), 30)
    clear_screen(stdscr)
    hide_cursor()
    try:
        inp = input.decode('UTF-8')  
        cur.noecho()
        return inp
    except:
        hide_cursor()
        cur.noecho()
        return default

def confirm_all(win, msg):
    return confirm(win, msg, acc = ['y','n','a']) 

def confirm(win, msg, acc = ['y','n']):
    c,_ = minput(win, 0, 1, 
            "Are you sure you want to " + msg + "? (" + "/".join(acc)  + ")",
            accept_on = acc)
    win.clear()
    win.refresh()
    return c.lower()

def minput(stdscr, row, col, prompt_string, accept_on = [], default=""):
    on_enter = False
    rows, cols = stdscr.getmaxyx()
    caps = cols - col - len(prompt_string) - 2
    if not accept_on:
        on_enter = True
        accept_on = [10, cur.KEY_ENTER]
    else:
        accept_on = [ord(ch) for ch in accept_on]
    show_cursor()
    cur.echo() 
    stdscr.keypad(True)
    stdscr.addstr(row, col, prompt_string)
    stdscr.clrtoeol()
    stdscr.refresh()
    out = default.split('\n')
    out = list(filter(None, out))
    line = 0
    if out:
        inp = str(out[0])
    else:
        inp = default
        out.append(inp)
    pos = len(inp)
    ch = 0
    start = col + len(prompt_string)
    while ch not in accept_on:
        stdscr.addstr(row, start, inp)
        stdscr.clrtoeol()
        pos = max(pos, 0)
        pos = min(pos, len(inp))
        xloc = start + pos
        yloc = row + (xloc // cols)
        xloc = xloc % cols
        stdscr.move(yloc, xloc)
        ch = stdscr.getch()
        if ch == 8 or ch == 127 or ch == cur.KEY_BACKSPACE:
            if pos > 0:
                inp = inp[:pos-1] + inp[pos:]
                pos -= 1
            else:
                mbeep()
        elif ch == cur.KEY_DC:
            if pos < len(inp):
                inp = inp[:pos] + inp[pos+1:]
            else:
                mbeep()
        elif chr(ch)=='<':
            if line == 0 and len(out) == 1:
                inp = ""
            else:
                del out[line]
                if line > len(out) - 1:
                    line = len(out) - 1
                inp = out[line]
        elif chr(ch) == ">":
            out[line] = inp
            line = line + 1
            out.insert(line, "")
            inp = ""
        elif ch == cur.KEY_HOME:
            pos = 0
        elif ch == cur.KEY_END:
            pos = len(inp)
        elif ch == cur.KEY_LEFT:
            if pos > 0:
                pos -= 1 
            else:
                mbeep()
        elif ch == cur.KEY_RIGHT:
            pos += 1
        elif ch == cur.KEY_UP: 
            if line == 0:
                break
            elif line == 0:
                mbeep()
            else:
                out[line] =inp
                line -= 1
                inp = out[line]
        elif ch == cur.KEY_DOWN:
            if line == len(out) - 1:
                break
            else:
                out[line] = inp
                line += 1
                inp = out[line]
        elif ch == 27:
            hide_cursor()
            cur.noecho()
            return "<ESC>",ch
        else:
            letter =chr(ch)
            if len(inp) >= caps:
                mbeep()
            elif on_enter:
                if letter.isalnum() or letter in ["'",'#','%','$','@','!','^','&','(',')', '*',' ',',','/','-','_',':','.','?','+']:
                    inp = inp[:pos] + letter + inp[pos:]
                    pos += 1
                else:
                    mbeep()
            else:
                if ch in accept_on:
                    inp = inp[:pos] + letter + inp[pos:]
                else:
                    mbeep()
    cur.noecho()
    hide_cursor()
    if len(out) == 0:
        return inp,ch  
    else:
        out[line] = inp
        return "\n".join(out), ch

def mbeep(repeat=1):
    if os.name == "nt":
        winsound.Beep(500, 100)
    else:
        cur.beep()

def get_key(stdscr = None):
    return stdscr.getch()

# -*- coding: utf-8 -*-
import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9]+)"

def rplit_into_sentences(text):
    sents = nltk.sent_tokenize(text)
    return sents

def qplit_into_sentences(text):
    try:
        import nltk
        try:
            sents = nltk.sent_tokenize(text)
            return sents
        except LookupError:
            nltk.download('punkt')
            sents = nltk.sent_tokenize(text)
            return sents
    except ImportError as e:
        return rplit_into_sentences(text)

def split_into_sentences(text, debug = False, limit = 2):
    text = " " + text + "  "
    text = text.replace("\n","<stop>")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = text.replace("[FRAG]","<stop>")
    text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = text.replace("et al.","et al<prd>")
    text = text.replace("e.g.","e<prd>g<prd>")
    text = text.replace("vs.","vs<prd>")
    text = text.replace("etc.","etc<prd>")
    text = text.replace("i.e.","i<prd>e<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" (\d+)[.](\d+) "," \\1<prd>\\2 ",text)
    text = text.replace("...","<prd><prd><prd>")
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    if len(sentences) > 1:
        sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences if len(s) > limit]
    return sentences
