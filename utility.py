import sys
import os
import getch as gh
import curses as cur

if os.name == 'nt':
    import msvcrt
    import ctypes

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
            stdscr.refresh()

def print_there(x, y, text, stdscr = None, color=0, attr = None, pad = False):
    if stdscr is not None:
        c = cur.color_pair(color)
        if attr is not None:
            c = cur.color_pair(color) | cur.A_BOLD
        height, width = stdscr.getmaxyx()
        #stdscr.addnstr(x, y, text, height*width-1, c)
        stdscr.addstr(x, y, text, c)
        if pad:
            pass #stdscr.refresh(0,0, x,y, height -5, width)
        else:
            stdscr.refresh()
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

def confirm(win, msg):
    c,_ = minput(win, 0, 1, 
            "Are you sure you want to " + msg + "? (y/n/a)",
            accept_on = ['y','Y','n','N','a'])
    return c.lower()

def minput(stdscr, row, col, prompt_string, accept_on = [], default=""):
    on_enter = False
    rows, cols = stdscr.getmaxyx()
    if not accept_on:
        on_enter = True
        accept_on = [10, cur.KEY_ENTER]
    else:
        accept_on = [ord(ch) for ch in accept_on]
    show_cursor()
    cur.echo() 
    stdscr.keypad(True)
    stdscr.addstr(row, col, prompt_string)
    stdscr.refresh()
    stdscr.clrtoeol()
    inp = str(default)
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
        if ch == 127 or ch == cur.KEY_BACKSPACE:
            if pos > 0:
                inp = inp[:pos-1] + inp[pos:]
                pos -= 1
            else:
                cur.beep()
        elif ch == cur.KEY_DC:
            if pos < len(inp):
                inp = inp[:pos] + inp[pos+1:]
            else:
                cur.beep()
        elif chr(ch)=='\\':
            inp = ""
        elif ch == cur.KEY_HOME:
            pos = 0
        elif ch == cur.KEY_END:
            pos = len(inp)
        elif ch == cur.KEY_LEFT:
            if pos > 0:
                pos -= 1 
            else:
                cur.beep()
        elif ch == cur.KEY_RIGHT:
            pos += 1
        elif ch == cur.KEY_UP or ch == cur.KEY_DOWN:
            hide_cursor()
            cur.noecho()
            return inp,ch
        elif ch == 27:
            hide_cursor()
            cur.noecho()
            return "<ESC>",ch
        else:
            letter =chr(ch)
            if on_enter:
                if letter.isalnum() or letter in ['#','%','$','@','!','^','&','(',')', '*',' ',',','/','-','_',':','.','?','+']:
                    inp = inp[:pos] + letter + inp[pos:]
                    pos += 1
                else:
                    cur.beep()
            else:
                if ch in accept_on:
                    inp = inp[:pos] + letter + inp[pos:]
                else:
                    cur.beep()
    cur.noecho()
    hide_cursor()
    return inp,ch  

def get_key(stdscr = None):
    if stdscr is not None:
        return stdscr.getch()
    else:
        first_char = gh.getch()
        if first_char == '\x1b':
            try:
                ret = {'[2':'insert','[3':'delete', '[H':'home','[F':'end', '[5':'pgup','[6':'pgdown','[A': 'up', '[B': 'down', '[C': 'right', '[D': 'left'}[gh.getch() + gh.getch()]
            except:
                ret = 'NA'
            return ret
        else:
            return first_char


# -*- coding: utf-8 -*-
import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9]+)"

import nltk
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
