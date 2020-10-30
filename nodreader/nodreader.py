import requests
import io
import subprocess, os, platform
import webbrowser
from datetime import date
import random
import datetime, time
from time import sleep
import sys, os 
import datetime
import pickle
import shlex
import re
import textwrap
import json
import urllib.request
try:
    from nodreader.util import *
except:
    from util import *
import curses as cur
from curses import wrapper
from curses.textpad import rectangle
from pathlib import Path
from urllib.parse import urlparse
from appdirs import *
import logging, sys
import traceback

appname = "NodReader"
appauthor = "App"

doc_path = os.path.expanduser('~/Documents/Nodreader')
app_path = user_data_dir(appname, appauthor)
logFilename = app_path + '/log_file.log'
Path(app_path).mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=logFilename, level=logging.DEBUG)

def handle_exception(exc_type, exc_value, exc_traceback):
    import sys
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    exc_info=(exc_type, exc_value, exc_traceback)
    logging.critical("\nDate:" + str(datetime.datetime.now()), exc_info=(exc_type, exc_value, exc_traceback))
    print("An error occured, check log file at ",app_path," to see the error details.")
    traceback.print_exception(*exc_info)

sys.excepthook = handle_exception

newspaper_imported = True
try:
    import newspaper
except ImportError as e:
    newspaper_imported = False


std = None
theme_menu = {}
theme_options = {}
template_menu = {}
template_options = {}

conf = {}
page = 0
query = ""
filters = {}

TEXT_COLOR = 100
ITEM_COLOR = 101
CUR_ITEM_COLOR = 102
SEL_ITEM_COLOR = 103
TITLE_COLOR = 104
INFO_COLOR = 105
ERR_COLOR = 106
HL_COLOR = 107
FAINT_COLOR = 108
MSG_COLOR = 109
TEMP_COLOR = 110
TEMP_COLOR2 = 111
COMMENT_COLOR = 32

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

color_map = {
        "text-color":TEXT_COLOR, 
        "back-color":TEXT_COLOR, 
        "item-color":ITEM_COLOR, 
        "cur-item-color":CUR_ITEM_COLOR,
        "sel-item-color":SEL_ITEM_COLOR,
        "title-color":TITLE_COLOR,
        "highlight-color":HL_COLOR,
        "faint-color":FAINT_COLOR,
        }
nod_color = {
        "yes":(147,148),
        "OK":(36,36),
        "agree":(22,22),
        "archive":(145,145),
        "okay":(29,36),
        "okay, okay!":(25,25),
        "okay?":(59,62),
        "not reviewed":(59,62),
        "goal":(22,22),
        "skipped":(244,245),
        "interesting!":(28,77),
        "important!":(97,98),
        "has an idea!":(114,115),
        "didn't get!":(89,90),
        "so?":(138,138),
        "okay, so?":(32,32),
        "explain more":(131,94),
        "why?":(58,59),
        "needs review":(63, 177),
        "review later":(63, 177),
        "to read later":(63, 177),
        "needs research":(94,179),
        "definition":(32,250),
        "got it!":(68,69),
        }

cW = 7
cR = 1
cG = 29
cY = 5
cB = 27  
cPink = 15
cC = 9 
clC = 16
clY = 13
cGray = 10
clGray = 250
clG = 12
cllC = 83
cO =  209
back_color = None


def reset_colors(theme, bg = None):
    global back_color
    if bg is None:
        bg = int(theme["back-color"])
    back_color = bg
    for each in range(1,min(256, cur.COLORS)):
        cur.init_pair(each, each, bg)
    cur.init_pair(TEXT_COLOR, int(theme["text-color"]) % cur.COLORS, bg)
    cur.init_pair(ITEM_COLOR, int(theme["item-color"]) % cur.COLORS, bg)
    cur.init_pair(CUR_ITEM_COLOR, bg, int(theme["cur-item-color"]) % cur.COLORS)
    cur.init_pair(SEL_ITEM_COLOR, int(theme["sel-item-color"]) % cur.COLORS, bg)
    cur.init_pair(TITLE_COLOR, int(theme["title-color"]) % cur.COLORS, bg)
    if theme["inverse-highlight"] == "True":
        cur.init_pair(HL_COLOR, bg, int(theme["highlight-color"]) % cur.COLORS)
    else:
        cur.init_pair(HL_COLOR, int(theme["highlight-color"]) % cur.COLORS, bg)
    cur.init_pair(FAINT_COLOR, int(theme["faint-color"]) % cur.COLORS, bg)
    cur.init_pair(ERR_COLOR, cW, cR % cur.COLORS)
    cur.init_pair(MSG_COLOR, cW, cB % cur.COLORS)
    cur.init_pair(INFO_COLOR, cW, cG % cur.COLORS)
    # for key,val in nod_color.items():
       # cur.init_pair(val[0], bg, val[0])


def scale_color(rtime):
    rtime = float(rtime)
    rtime *= 4
    if rtime == 0:
        return 255
    elif rtime < 1:
        return 34
    elif rtime < 2:
        return 76
    elif rtime < 3:
        return 119
    elif rtime < 4:
        return 186
    elif rtime < 5:
        return 190
    elif rtime < 6:
        return 220 
    elif rtime < 7:
        return 208
    elif rtime < 8:
        return 202
    else:
        return 124

    
def openFile(filepath):
    _file = Path(filepath)
    if _file.is_file(): 
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filepath))
        show_info("File was opened externally")
    else:
        show_err(str(filepath) + " doesn't exist, you can download it by hitting d key")

def delete_file(art):
    if "save_folder" in art:
        fname = art["save_folder"]
    else:
        title = art["title"]
        file_name = title.replace(' ','-')[:50] + ".pdf"#url.split('/')[-1]
        folder = doc_path
        if folder.endswith("/"):
            folder = folder[:-1]

        fname = folder + "/" + file_name
    _file = Path(fname)
    if _file.is_file():
        _file.unlink()
        show_info("File was deleted")
    else:
        show_info("File wasn't found on computer")

def download(url, art, folder):
    if not url.endswith("pdf"):
        webbrowser.open(url)
        return

    title = art["title"]
    file_name = title.replace(' ','-')[:50] + ".pdf"#url.split('/')[-1]

    # Streaming, so we can iterate over the response.
    folder = doc_path + "/" + folder

    if folder.endswith("/"):
        folder = folder[:-1]

    Path(folder).mkdir(parents=True, exist_ok=True)

    fname = folder + "/" + file_name
    _file = Path(fname)
    if _file.is_file(): 
        openFile(_file)
        art["save_folder"] = str(_file)
    else:
        show_info("Starting download ... please wait")
        sleep(0.1)
        with urllib.request.urlopen(url) as Response:
            Length = Response.getheader('content-length')
            BlockSize = 1000000  # default value

            if not Length:
                show_err("ERROR, zero file size,  something went wrong")
                return
            else:
                Length = int(Length)
                BlockSize = max(4096, Length // 20)

            show_info("UrlLib len, blocksize: " + str(Length) + " " + str(BlockSize))

            BufferAll = io.BytesIO()
            Size = 0
            try:
                while True:
                    BufferNow = Response.read(BlockSize)
                    if not BufferNow:
                        break
                    BufferAll.write(BufferNow)
                    Size += len(BufferNow)
                    if Length:
                        Percent = int((Size / Length)*100)
                        show_info(f"download: {Percent}% {url}")

                _file.write_bytes(BufferAll.getvalue())
                show_info("File was written to " + str(_file))
                art["save_folder"] = str(_file)
                openFile(_file)

            except Exception as e:
                show_err("ERROR:"+ str(e))


def save_obj(obj, name, directory):
    if name.strip() == "":
        logger.info("Empty object to save")
        return
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    Path(folder).mkdir(parents=True, exist_ok=True)
    fname = folder + '/' + name + '.pkl'
    with open(folder + '/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name, directory, default=None):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    fname = folder + '/' + name + '.pkl'
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return default 
    with open(fname, 'rb') as f:
        return pickle.load(f)

def is_obj(name, directory):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    if not name.endswith('.pkl'):
        name = name + '.pkl'
    fname = folder + '/' + name 
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return False 
    else:
        return True

def del_obj(name, directory):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    if not name.endswith('.pkl'):
        name = name + '.pkl'
    fname = folder + '/' + name 
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return None 
    else:
        obj_file.unlink()

def get_index(articles, art):
    i = 0
    for a in articles:
        if a["id"] == art["id"]:
           return i
        i += 1
    return -1

def remove_article(articles, art):
    i = get_index(articles, art) 
    if i >= 0:
       articles.pop(i)

def insert_article(articles, art):
    i = get_index(articles, art) 
    if i < 0:
        articles.insert(0, art)
    else:
        articles.pop(i)
        articles.insert(0, art)

def update_article(articles, art):
    insert_article(articles, art) 

def get_title(text, default="No title"):
    text = text.strip()
    text = "\n" + text
    parts = text.split("\n# ")
    if len(parts) > 1:
        part = parts[1]
        end = part.find("\n")
        return part[:end], end + 2
    else:
        return default, -1

def get_sects(text):
    text = text.strip()
    text = "\n" + text
    sects = text.split("\n## ")
    ret = []
    if len(sects) == 1:
        new_sect = {}
        new_sect["title"] = "all"
        new_sect["fragments"] = get_frags(sects[0])
        ret.append(new_sect)
    else:
        for sect in sects[1:]:
            new_sect = {}
            end = sect.find("\n")
            new_sect["title"] = sect[:end]
            frags = sect[end:]
            new_sect["fragments"] = get_frags(frags)
            ret.append(new_sect)
    return ret

def get_frags(text):
    text = text.strip()
    parts = text.split("\n")
    parts = list(filter(None, parts)) 
    frags = []
    for t in parts:
        frag = {"text":t}
        frags.append(frag)
    return frags

def remove_tag(art, fid, saved_articles):
    if "tags" in art:
        for i, tag in enumerate(art["tags"]):
            if tag == fid:
                art["tags"].pop(i)
                update_article(saved_articles, art)
                save_obj(saved_articles, "saved_articles", "articles")
                break

def request(p = 0):
     
    global page
    show_info("Searching ... please wait...")
    page = int(p)
    size = 15
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://dimsum.eu-gb.containers.appdomain.cloud',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://dimsum.eu-gb.containers.appdomain.cloud/',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    size = int(size)
    filters_str = json.dumps(filters)
    data = f'{{"query":"{query}","filters":{filters_str},"page":{page},"size":{size},"sort":null,"sessionInfo":""}}'
    #data ='{"query":"reading comprehension","filters":{},"page":0,"size":30,"sort":null,"sessionInfo":""}'

    # return [], data
    try:
        response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)
    except requests.exceptions.HTTPError as errh:
        return [],("Http Error:" + str(errh))
    except requests.exceptions.ConnectionError as errc:
        return [],("Error Connecting:" + str(errc))
    except requests.exceptions.Timeout as errt:
        return [],("Timeout Error:" + str(errt))
    except requests.exceptions.RequestException as err:
        return [],("OOps: Something Else" + str(err))

    try:
        rsp = response.json()['searchResults']['results'],""
    except:
        return [], "Corrupt or no response...."
    return rsp,""

def list_articles(in_articles, fid, show_nod = False, group="", filter_nod =""):
    global template_menu

    if len(in_articles) <= 0:
        return "There is no article to list!"

    articles = in_articles
    if filter_nod != "":
        articles = []
        for art in in_articles:
            if "nods" in art and art["nods"][0] == filter_nod:
                articles.append(art)
    rows, cols = std.getmaxyx()
    main_win = cur.newpad(rows*50, cols)
    width = cols - 10
    main_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    sel_arts = []
    saved_articles = load_obj("saved_articles", "articles", [])
    tags = load_obj("tags","")
    ch = 0
    start = 0
    k = 0
    ni = 0
    while ch != ord('q'):
        main_win.erase()
        mprint("", main_win)
        mprint(fid + " " + query, main_win, cW)
        N = len(articles)
        cc = start
        jj = start
        while cc < start + 15 and jj < len(articles): 
            a = articles[jj]
            saved_index = get_index(saved_articles, a)
            if saved_index > 0:
                a = articles[cc] = saved_articles[saved_index]
            if "year" in a:
                h = a['year']
            else:
                h = cc
            color = ITEM_COLOR
            art_nod = ""
            if "nods" in a and a["nods"][0] != "":
                nod = a["nods"][0]
                color = nod_color[nod][1]  % cur.COLORS if nod in nod_color else TEXT_COLOR
                art_nod = " [" + nod + "]"

            if a in sel_arts:
                color = SEL_ITEM_COLOR
            if cc == k:
                color = CUR_ITEM_COLOR

            paper_title =  a['title']
            dots = ""
            if len(paper_title + art_nod) > width - 40:
               dots = "..."
            item = "[{}] {}".format(h, paper_title[:width - 40] + art_nod + dots)               

            mprint(item, main_win, color)
            _list = "nods"
            if show_nod and fid == "comments":
                _list = "comments"
            if show_nod and _list in a and "sents" in a:
                for i,note in enumerate(a[_list]):
                    if (fid == "comments" and note != "") or note == fid:
                        sent = textwrap.indent(textwrap.fill(str(i) + ") " + a["sents"][i]),'  ')
                        mprint(sent, main_win, TEXT_COLOR)
                        if fid == "comments":
                            mprint(note, main_win, COMMENT_COLOR)
                        mprint("", main_win)

            cc += 1
            jj += 1
            # Endf while
        rows, cols = std.getmaxyx()
        main_win.refresh(0,0, 2, 5, rows - 2, cols - 6)
        _p = k // 15
        all_pages = (N // 15) + (1 if N % 15 > 0 else 0) 
        show_info("Enter) view article       PageDown) next page (load more...)     h) other commands " + str(N) + " " + str(N))
        print_there(0, cols - 15, "|" + str(N) + "|" + str(_p + 1) +  " of " + str(all_pages), win_info, INFO_COLOR)
        ch = get_key(std)
        if ch == cur.KEY_ENTER or ch == 10:
            k = max(k, 0)
            k = min(k, N-1)
            main_win.erase()
            main_win.refresh(0,0, 2, 5, rows - 3, cols - 6)
            if show_nod:
                show_article(articles[k], fid)
            else:
                show_article(articles[k])

        if ch == cur.KEY_UP:
            if k > 0:
                k -= 1
            else:
                mbeep()
        if ch == cur.KEY_DOWN:
            if k < N -1:
                k +=1
            else:
                mbeep()

        if k >= start + 15 and k < N:
            ch = cur.KEY_NPAGE
        if k < start:
            ch = "prev_pg"

        if ch == cur.KEY_PPAGE or ch == 'prev_pg':
            start -= 15
            start = max(start, 0)
            k = start + 14 if ch == 'prev_pg' else start
        elif ch == cur.KEY_NPAGE:
            start += 15
            if start > N - 15:
                show_info("Getting articles for "+ query)
                new_articles, ret = request(page + 1)
                if len(new_articles) > 0 and ret == "":
                    if isinstance(new_articles, tuple):
                        new_articles = new_articles[0]
                    articles = articles + new_articles
                    save_obj(articles, "last_results", "")
                    N = len(articles)
                else:
                    #ret = textwrap.fill(ret[:200], initial_indent='', subsequent_indent='    ')
                    show_err(ret[:200]+ "...", bottom = False)
            start = min(start, N - 15)
            k = start
        elif ch == cur.KEY_HOME:
            k = start
        elif ch == cur.KEY_END:
            k = N -1 #start + 14
            mod = 15 if N % 15 == 0 else N % 15
            start = N - mod 

        if ch == ord('h'):
            show_info(('\n'
                       ' s)          select/deselect an article\n'
                       ' a)          select all articles\n'
                       " Left)          filter the articles by the title's nod \n"
                       ' t)          tag the selected items\n'
                       ' d)          delete the selected items from list\n'
                       ' w)          write the selected items into files\n'
                       ' p)          select the output file format\n'
                       ' m)          change the color theme\n'
                       ' HOME)       go to the first item\n'
                       ' END)        go to the last item\n'
                       ' PageUp)     previous page\n'
                       ' Arrow keys) next, previous article\n'
                       ' q)          return back to the search menu\n'),
                       bottom=False)
        if  ch == ord('s'):
            if not articles[k] in sel_arts:
                sel_arts.append(articles[k])
            else:
                sel_arts.remove(articles[k])
        if ch == ord('n') or ch == cur.KEY_LEFT:
            if filter_nod != '':
                ch = ord('q')
            else:
                tmp = sel_nod(5, 10, ni, 0)
                _nod = tmp if tmp != "NULL" else ""
                if _nod != "":
                    list_articles(articles, fid, show_nod, group, _nod)
        if ch == ord('a'):
            for ss in range(start,min(N, start+15)):
                  art = articles[ss]
                  if not art in sel_arts:
                      sel_arts.append(art)
                  else:
                      sel_arts.remove(art)
        if ch == ord('d') and group =="tags":
            if not sel_arts:
                art = articles[k]
                if len(art["tags"]) == 1:
                    _confirm = confirm_all(win_info, "remove the last tag of " + art["title"][:20])
                    if _confirm == "y" or _confirm == "a":
                        remove_tag(art, fid, saved_articles)
                        articles.remove(art)
                else:
                    remove_tag(art, fid, saved_articles)
                    articles.remove(art)
            else:
                _confirm = ""
                for art in sel_arts:
                    if len(art["tags"]) == 1:
                        if _confirm != "a":
                            _confirm = confirm_all(win_info, "remove the last tag of " + art["title"][:20])
                        if _confirm == "y" or _confirm == "a":
                            remove_tag(art, fid, saved_articles)
                            articles.remove(art)
                    else:
                        remove_tag(art, fid, saved_articles)
                        articles.remove(art)
                sel_arts = []
            N = len(articles)
            k = 0

        if ch == ord('p'):
            choice = ''
            mi = 0
            while choice != 'q':
                choice, template_menu, mi = show_menu(template_menu, template_options, title="template", mi = mi, shortkeys = {"s":"save as"})
            save_obj(template_menu, conf["template"], "tempate")

        if ch == ord('t'):
            if not sel_arts:
                show_err("No article was selected")
            else:
                tag,_ = minput(win_info, 0, 1, "Please enter a tag for selected articles:", default = query) 
                tag = tag.strip()
                if tag != "<ESC>" and tag != "":
                    if not tag in tags:
                        tags.append(tag)
                        save_obj(tags, "tags", "")
                    for a in sel_arts:
                        if not "tags" in a:
                            a["tags"] = [tag]
                        elif not tag in a["tags"]:
                            a["tags"].append(tag)
                        insert_article(saved_articles, a)
                        save_obj(saved_articles, "saved_articles", "articles")
                        show_info("Selected articles were added to tagged articles ")
                    sel_arts = []
        if ch == ord('w'): 
            if not sel_arts:
                show_err("No article was selected!! Select an article using s")
            else:
                fid,_ = minput(win_info, 0, 1," Folder name (relative to documents root):", default = fid)
                for a in sel_arts:
                    write_article(a, fid)
                show_msg(str(len(sel_arts))+ " articles were downloaded and saved into:" + fid)

def replace_template(template, old_val, new_val):
    ret = template.replace("{newline}","\n")
    ret = ret.replace(old_val,new_val)
    return ret

def write_article(article, folder=""):
    ext = '.' + template_menu["preset"]
    _folder = doc_path + "/" +  template_menu["preset"] + "/" + folder 
    if not os.path.exists(_folder):
        os.makedirs(_folder)
    top = replace_template(template_menu["top"],"{url}", article["pdfUrl"])
    bottom = replace_template(template_menu["bottom"],"{url}", article["pdfUrl"])
    paper_title = article['title']
    file_name = paper_title.replace(' ','_').lower()
    fpath = _folder + '/' + file_name + ext
    f = open(fpath, "w")
    print(top, file=f)
    title = replace_template(template_menu["title"],"{title}",paper_title)
    print(title, file=f)
    for b in article['sections']:
        sect_title =  b['title']
        sect_title = replace_template(template_menu["section-title"],"{section-title}",sect_title)
        print(sect_title, file=f)
        for c in b['fragments']:
            text = c['text']
            text = replace_template(template_menu["paragraph"],"{paragraph}", text)
            f.write(text)
    print(bottom, file=f)
    f.close()
    show_info("Artice was writen to " + fpath + '...')

def sel_nod(ypos, left, ni, si):
    nod_win = cur.newwin(12, 60, ypos + 2, left)
    nod_win.bkgd(' ', cur.color_pair(INFO_COLOR)) # | cur.A_REVERSE)
    opts = [] #load_obj("nod_opts","")
    if si == 0:
        opts.append(["interesting!", "important!", "needs review", "needs research", "got it!", "didn't get!", "archive", "not reviewed", "to read later", "skipped"])
    elif not opts:
        opts.append(["interesting!", "important!", "has an idea!",  "okay, so?", "explain more", "why?", "didn't get!", "needs review", "needs research", ""])
        opts.append(["definition", "goal", "support", "example"])
        save_obj(opts, "nod_opts", "")

    ni, stack_index = select_box(nod_win, opts, ni, stack_index = 0, in_row = True)
    if ni >= 0:
        _nod = opts[stack_index][ni]
        if _nod == "custom":
            custom_nod,_ = minput(win_info, 0, 1, "Enter a note or a nod (<Esc> to cancel):") 
            _nod = custom_nod if custom_nod != "<ESC>" else ""
            if _nod != "":
                opts.append(_nod)
                save_obj(opts, "nod_opts", "")
        nod_win.erase()
        return _nod
    else:
        nod_win.erase()
        return 'NULL'

def print_nod(text_win, nods, fsn, si, bmark, width):
   if nods[fsn] in nod_color:
       d_color,l_color = nod_color[nods[fsn]]
   else:
       d_color,l_color = TEXT_COLOR, TEXT_COLOR
   if nods[fsn] != "" and nods[fsn] != "next":
       if fsn > 0 and fsn >= bmark and fsn <= si:
           tmp = nods[fsn].ljust(width-2) 
           cur.init_pair(TEMP_COLOR, back_color, d_color % cur.COLORS)
           mprint(tmp, text_win,TEMP_COLOR)
       else:
           mprint(nods[fsn], text_win, l_color % cur.COLORS) 

def show_article(art, show_nod=""):
    global theme_menu, theme_options, query, filters
    total_sects = 0
    sel_sects = {}
    sel_arts = []
    k,sc  = 0,0
    fast_read = False
    show_prev = False
    break_to_sent = False 
    start_row = 0
    rows, cols = std.getmaxyx()
    width = 2*cols // 3 
    text_win = cur.newpad(rows*50, cols -1)
    text_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)

    # text_win = std
    bg = ""
    saved_articles = load_obj("saved_articles", "articles", [])
    expand = 3
    frags_text = ""
    art_id = -1
    fc = 1
    cury = 0
    page_height = rows - 4
    scroll = 1
    show_reading_time = False
    start_reading = True
    figures_created = False
    cur_sent = "1"
    is_section = False
    art_id = art['id']
    
    sc = 0
    fc = 1
    si = 0
    bmark = 0
    frags_sents = {}
    frags_sents[0] = (0, art["title"])
    fsn = 1
    ffn = 1
    nods = []
    has_nods = False
    if "nods" in art:
       nods = art["nods"]
       has_nods = True
    else:
        nods.append("not reviewed")
    comments = []   
    if "comments" in art:
        comments = art["comments"]
    visible = {}
    art["sents"] = {}
    visible[0] = True
    art["sents"][0] = art["title"]
    last_sect = -1
    for b in art["sections"]:
        frags_text = ""
        b['frags_offset'] = ffn
        b["sents_offset"] = fsn
        frags_sents[ffn] = (fsn, b["title"])
        art["sents"][fsn] = b["title"]
        last_sect = fsn
        visible[fsn] = True if show_nod == '' else False
        ffn += 1
        fsn += 1
        for c in b['fragments']:
            text = c['text']
            sents = split_into_sentences(text)
            frags_sents[ffn] = (fsn, sents)
            c['sents_offset'] = fsn 
            c['sents_num'] = len(sents)
            for sent in sents:
                art["sents"][fsn] = sent
                visible[fsn] = True
                if show_nod == "comments" and comments:
                    if comments[fsn] != "":
                        visible[last_sect] = True
                    else:
                        visible[fsn] = False
                elif has_nods:
                    if show_nod == nods[fsn]:
                        visible[last_sect] = True
                    elif show_nod != '':
                        visible[fsn] = False
                elif not has_nods:
                    if fsn % 3 == 0:
                        nods.append("")
                    else:
                        nods.append("")
                fsn += 1
            if not has_nods:
                nods.append("")
            ffn += 1
        if not has_nods:
            nods.append("")
        b["sents_num"] = fsn - b["sents_offset"]
        b['frags_num'] = len(b["fragments"])
    total_sents = fsn 
    total_frags = ffn
    si = 2
    fc = 2
    if si >= total_sents -1:
        si = 0

    if bmark < si:
        bmark = si

    ch = 0
    main_info = "o) download/open externally  r) resume reading f) list figures h) list commands "
    show_info(main_info)
    ni,fi = 0,0
    passable = [False]*total_sents
    if not "comments" in art:
       comments = [""]*total_sents
    if "times" in art:
       rtime = art["times"]
    else:
       rtime = {} 
    pos = [0]*total_sents
    art_changed = False
    art_changed = False
    show_info("r) resume from last position")
    figures = []
    if "figures" in art:
        figures = art["figures"]
    nod_set = False
    needs_nod = False
    while ch != ord('q') and ch != 127:
        # clear_screen(text_win)
        text_win.erase()
        start_row = max(0, start_row)
        start_row = min(cury - 1, start_row)
        if bg != theme_menu["back-color"]:
            bg = theme_menu["back-color"]
            clear_screen(std)
            #text_win.refresh(start_row,0, 0,0, rows-1, cols-1)
            show_info(main_info)
            text_win.erase()
        start_time = time.time()
        sn = 0
        total_sects = len(art["sections"])
        sc = max(sc, 0)
        sc = min(sc, total_sects)
        title = "\n".join(textwrap.wrap(art["title"], width)) # wrap at 60 characters
        pdfurl = art["pdfUrl"]
        top =  "["+str(k)+"] " + title 
        if si == 0:
            mprint(top,  text_win, HL_COLOR, attr = cur.A_BOLD) 
            cur_sent = top
        else:
            mprint(top,  text_win, TITLE_COLOR, attr = cur.A_BOLD) 
        print_nod(text_win, nods, 0, 0, 0, width)
        mprint(pdfurl,  text_win, TITLE_COLOR, attr = cur.A_BOLD) 
        if comments[0] != "":
            com = textwrap.wrap(comments[0], width=width-5, replace_whitespace=False)
            com = "\n".join(com)
            mprint(com, text_win, COMMENT_COLOR)
        pos[0],_ = text_win.getyx()
        passable[0] = False
        mprint("", text_win)
        fsn = 1
        ffn = 1
        is_section = False
        for b in art["sections"]:
            fragments = b["fragments"]
            fnum = len(fragments)
            _color = ITEM_COLOR
            if fsn == si:
                cur_sent = b["title"]
                is_section = True
                _color = HL_COLOR
            if sn == sc:
                sect_fc = fc - b["frags_offset"] + 1
                sect_title = b["title"] # + f"({sect_fc+1}/{fnum})" 
                if fsn != si:
                    if art_id in sel_sects and b["title"].lower() in sel_sects[art_id]:
                        _color = HL_COLOR
                    else:
                        _color = SEL_ITEM_COLOR
            else:
                sect_title = b["title"]
 
            if visible[fsn] and sect_title != "all":
                mprint(sect_title, text_win, _color, attr = cur.A_BOLD)

            pos[fsn],_ = text_win.getyx()
            passable[fsn] = True
            ffn += 1
            fsn += 1
            if expand == 0:
                fsn += b["sents_num"] 
                ffn += len(b["fragments"])
            else:
                # mprint("", text_win)
                for frag in fragments:
                    if ffn != fc and expand == 1:
                        fsn += frag['sents_num']
                        ffn += 1
                    else:
                       if not ffn in frags_sents:
                           frag_sents = split_into_sentences(frag['text'])
                           frags_sents[ffn] = (fsn, frag_sents)
                       else:
                           frag_sents = frags_sents[ffn][1]
 
                       # if "level" in frag:
                          # color = frag["level"] % 250
                       hlcolor = HL_COLOR
                       color = FAINT_COLOR
                       if True:
                           for sent in frag_sents:
                               nods[fsn] = "okay" if nods[fsn] == "OK" else nods[fsn]
                               feedback = nods[fsn] + " " + comments[fsn]
                               if show_nod == "comments":
                                   if comments[fsn] != "":
                                       visible[fsn] = True
                                       tfsn = fsn - 1
                                       while tfsn > 0 and nods[tfsn] == "next":
                                           visible[tfsn] = True
                                           tfsn -= 1
                                   else:
                                       visible[fsn] = False
                               elif (show_nod != "" and not show_nod in feedback) or nods[fsn] == "remove":
                                   visible[fsn] = False
                               elif show_nod != "" and nods[fsn] != "remove":
                                   visible[fsn] = True
                                   tfsn = fsn - 1
                                   while tfsn > 0 and nods[tfsn] == "next":
                                       visible[tfsn] = True
                                       tfsn -= 1

                               if not visible[fsn]: 
                                   pos[fsn],_ = text_win.getyx()
                                   fsn +=1 
                                   continue

                               #cur.init_pair(NOD_COLOR,back_color,cG)
                               reading_time = rtime[fsn][1] if fsn in rtime else 0 
                               f_color = HL_COLOR
                               hline = "-"*(width)
                               if show_reading_time:
                                   f_color = scale_color(reading_time)
                                   mprint(str(reading_time), text_win, f_color)
                               lines = textwrap.wrap(sent, width-4) 
                               lines = filter(None, lines)
                               end = ""
                               sent = ""
                               # sent += " "*(width -2) + "\n"
                               for line in lines:
                                   sent += "  " + line.ljust(width-4)+"\n" 
                               #sent += " "*(width - 2) + "\n"
                               if nods[fsn] == "" or nods[fsn] == "next":
                                   pass
                                   #sent += " "*(width -2) + "\n"
                               if fsn >= bmark and fsn <= si and not passable[fsn]:
                                   hl_pos = text_win.getyx() 
                                   cur_sent = sent
                                   hlcolor = HL_COLOR
                                   if theme_menu["bold-highlight"]== "True":
                                       mprint(sent, text_win, hlcolor, attr=cur.A_BOLD, end=end)
                                   else:
                                       mprint(sent, text_win, hlcolor, end=end)
                               else:
                                   mprint(sent, text_win, color, end=end)
                               if feedback != '' and passable[fsn] == False:
                                   print_nod(text_win, nods, fsn, si, bmark, width)

                                   if comments[fsn] != "":
                                       if False: #fsn >= bmark and fsn <= si:
                                           tmp = comments[fsn].ljust(width-2) 
                                           cur.init_pair(TEMP_COLOR2, back_color, COMMENT_COLOR % cur.COLORS)
                                           mprint(tmp, text_win, TEMP_COLOR2, end = "\n")
                                       else:
                                           com = textwrap.wrap(comments[fsn], 
                                                   width=width-5, replace_whitespace=False)
                                           com = "\n".join(com)
                                           mprint(com, text_win, COMMENT_COLOR, end = "\n")
                                       #mprint(" "*(width-3), text_win, HL_COLOR)
                               else:
                                   pass # mprint("", text_win, f_color)
                               pos[fsn],_ = text_win.getyx()
                               fsn += 1
                       
                       if fsn >= bmark and fsn <= si:
                           mprint(" "*(width-2), text_win, HL_COLOR)
                       else:
                           mprint(" ", text_win, color)
                       ffn += 1
                     # end for fragments
            sn += 1
         # end for sections
 
        #print(":", end="", flush=True)
        cury, curx = text_win.getyx()
        sc = min(sc, total_sects)
        f_offset = art['sections'][sc]['frags_offset'] 
        offset = art["sections"][sc]["sents_offset"] 
        # show_info("frags:"+ str(total_frags) + " start row:" + str(start_row) + " frag offset:"+ str(f_offset)  + " fc:" + str(fc) + " si:" + str(si) + " sent offset:" + str(offset))
        if not (ch == ord('.') or ch == ord(',')): 
            if pos[bmark] > rows // 3:    
                start_row = pos[bmark] - rows //3 
            else:
                start_row = 0

        #if ch != cur.KEY_LEFT:
        rows, cols = std.getmaxyx()
        #width = 2*cols // 3 
        left = (cols - width)//2
        text_win.refresh(start_row,0, 2,left, rows -2, cols-1)
        ch = get_key(std)
        show_info(main_info)
        if ch == ord('+'):
            if width < 2*cols // 3: 
                text_win.erase()
                text_win.refresh(0,0, 2,0, rows -2, cols-1)
                width +=2
            else:
                mbeep()
        if ch == ord('-'):
            if width > cols // 3:
                text_win.erase()
                text_win.refresh(0,0, 2,0, rows -2, cols-1)
                width -= 2
            else:
               mbeep()
        if ch == ord('n'):
            if show_nod != '':
                show_nod = ''
                visible = [True]*total_sents
            else:
                ypos = pos[bmark]-start_row
                tmp = sel_nod(ypos, left, ni, 0)
                show_nod = tmp if tmp != "NULL" else ""
        if ch == ord('o'):
            if "save_folder" in art and art["save_folder"] != "":
                fname = art["save_folder"]
                _file = Path(fname)
                if _file.is_file():
                    openFile(_file)
                else:
                    show_msg(str(_file) + " was not found")
                    art["save_folder"] = ""
            else:
                fid,_ = minput(win_info, 0, 1," Folder name (relative to documents root, you can leave it blank):", default = "") 
                if fid != "<ESC>":
                    download(art["pdfUrl"], art, fid)
        if ch == ord('d'):
            _confirm = confirm(win_info, "delete the pdf file from your computer")
            if _confirm == "y" or _confirm == "a":
                delete_file(art)
                art["save_folder"] = ""
        if ch == cur.KEY_DC:
            mbeep()
            nods[si] = "remove"
            ch = cur.KEY_DOWN
        if ch == ord('y'):
            with open(art["title"]  + ".txt","w") as f:
                print(art, file = f)
        if ch == ord('r'):
           si = total_sents - 1 
           while (nods[si] == "" or not visible[si]) and si > 2:
               si -= 1
           si = max(si, 1)
           bmark = si 
           update_si = True

        if ch == ord('v'):
            _confirm = confirm(win_info, "restore the removed parts")
            if _confirm == "y" or _confirm == "a":
                visible = [True]*total_sents
            for i,nod in enumerate(nods):
                if nod == "remove":
                    nods[i] = ""
            art_changed = True
        if ch == ord('z'):
            show_reading_time = not show_reading_time

        if ch == ord('h'):
            show_info(('\n'
                       '  Down)          expand the selection to next sentence\n'
                       '  Right)         nod the selected sentences with "okay"\n'
                       '  Left)          select from other nods\n'
                       '  o)             download/open the pdf file externally\n'
                       '  f)             list figures\n'
                       '  t)             tag the article\n'
                       '  d)             delete the external pdf file \n'
                       '  w)             write the article into a file\n'
                       '  p)             select the output file format\n'
                       '  m)             change the color theme\n'
                       '  u)             reset comments and nods\n'
                       '  DEL)           remove selected sentence\n'
                       '  v)             restore removed sentences\n'
                       '  n)             filter sentences by a nod\n'
                       '  +/-)           increase/decrease the width of text\n'
                       '  :)             add a comment \n'
                       '  k/j)           previous/next section\n'
                       '  l/;)           previous/next fragment\n'
                       '  PgUp/PgDown)   previous/next page\n'
                       '  h)             show this list\n'
                       '  q)             close \n'
                       ''),
                       bottom=False)
            text_win.erase()
            text_win.refresh(0,0, 0,0, rows-1, cols-1)
        if ch == ord('x'):
            fast_read = not fast_read
        if ch == ord('w'):
            fid,_ = minput(win_info, 0, 1," Folder name (relative to documents root, you can leave it blank):", default = "") 
            if fid != "<ESC>":
                write_article(art, fid)
            show_msg("The article was written in " + fid)
        if ch == ord('u'):
            _confirm = confirm(win_info, "reset the article")
            if _confirm == "y" or _confirm == "a":
                nods = [""]*total_sents
                comments = [""]*total_sents
                rtime = {} 
                visible = [True]*total_sents
                passable = [False]*total_sents
                si = 2
                art_changed = True
                update_si = True
        if ch == ord('e'):
            if expand < 3:
                expand += 1
            else:
                expand = 0

        if ch == ord('s'):
            cur_sect = art["sections"][sc]["title"].lower()
            if art_id in sel_sects:
                if cur_sect in sel_sects[art_id]:
                    sel_sects[art_id].remove(cur_sect)
                else:
                    sel_sects[art_id].append(cur_sect)
            else:
                sel_sects[art_id] = [cur_sect]

        if ch == cur.KEY_LEFT or ch == cur.KEY_RIGHT or ch == cur.KEY_DOWN:
            _nod = nods[si] 
            if ch == cur.KEY_DOWN and needs_nod and not nod_set:
               for ii in range(bmark, si + 1):
                   if ii < si:
                       nods[ii] = "next"
               nods[si] = "skipped"
               nod_set = True
            else:
                nod_set = False
            if ch == cur.KEY_RIGHT:
                #if _nod == "" or _nod == "next":
                _nod = "okay"
                nod_set = True
            elif ch == cur.KEY_LEFT:
                ypos = pos[bmark]-start_row
                tmp_nod = sel_nod(ypos, left, ni, si)
                if tmp_nod != 'NULL':
                    _nod = tmp_nod
                    nod_set = True

            if ch == cur.KEY_LEFT or ch == cur.KEY_RIGHT:  
                for ii in range(bmark, si + 1):
                    if ii < si:
                        nods[ii] = "next"
                    if _nod == "remove":
                        visible[ii] = False
                if visible[si] and (nods[si] == "" or nod_set):
                    nods[si] = _nod

                end_time = time.time()
                cur_sent_length = len(cur_sent.split()) 
                if cur_sent_length == 0:
                    cur_sent_length = 0.01
                reading_time = (end_time - start_time)/cur_sent_length
                reading_time = round(reading_time, 2)
                tries = 0
                if si in rtime:
                    avg = rtime[si][1]
                    tries = rtime[si][0] + 1
                    reading_time = avg + 1/tries*(reading_time - avg)

                rtime[si] = (tries, reading_time)
            can_inc = True
            next_frag_start = frags_sents[fc + 1][0] if fc+1 < total_frags else total_sents 
            if ch == cur.KEY_DOWN and not nod_set and ((si - bmark) >= 2 or si + 1 >= next_frag_start):
                can_inc = False
            if si < total_sents - 1:
                if si <= 1 or (nods[si] != "" and nods[si] != "next"):
                    can_inc = True
                    nod_set = True
            if si  < total_sents - 1 and can_inc:
                if ch == cur.KEY_DOWN: # or ch == cur.KEY_RIGHT or nod_set:
                    tmp_si = si
                    si += 1
                    while si < total_sents and (not visible[si] or passable[si] or nods[si]=="next"):
                        si += 1
                    if si == total_sents:
                        si = tmp_si
                        mbeep()
                    
                if ch == cur.KEY_DOWN and nod_set:
                    bmark = si
                    while bmark >=0 and nods[bmark - 1] == "next":
                        bmark -= 1
                needs_nod = False
            else:
                needs_nod = True
                for ii in range(bmark, si + 1):
                   if ii < si:
                       nods[ii] = "next"
                nods[si] = "skipped"
                nod_set = True
                nods[si] = "okay?"
                mbeep()
                show_info("Please use the <Left> or <Right> arrow keys to nod the sentence, and <Down> to skip.", MSG_COLOR)
                if si > total_sents - 1:
                    si = total_sents - 1

        art_changed  = art_changed or nod_set
        if ch == cur.KEY_UP:
            if si > 0: 
                si -= 1
                while si > 0 and (not visible[si] or passable[si]):
                    si -= 1
                if bmark >= si:
                    bmark = si
                    while bmark >=0 and nods[bmark - 1] == "next":
                        bmark -= 1
            else:
                mbeep()
                si = 0

        update_si = False
        if ch == ord('j'):
            if sc > 0:
                sc -= 1
                fc = art["sections"][sc]["frags_offset"] + 1 
                update_si = True
            else:
                mbeep()
                sc = 0
        if ch == ord('k'):
            if sc < total_sects - 1:
                sc += 1
                fc = art["sections"][sc]["frags_offset"] + 1
                update_si = True
            else:
                mbeep()
                sc = total_sects -1
                fc = art["sections"][sc]["frags_offset"] + 1
                update_si = True
        if ch == ord(';'):
            if fc < total_frags - 1:
                fc += 1
                _tmp = frags_sents[fc][0]
                if passable[_tmp]:
                    fc += 1
                update_si = True
            else:
                mbeep()
                fc = total_frags -1
        if ch == ord('l'):
            if fc > 0 :
                fc -= 1
                _tmp = frags_sents[fc][0]
                if passable[_tmp]:
                    fc -= 1
                update_si = True
            else:
                mbeep()
                fc = 0

        if ch == ord('.'):
            if start_row < cury:
                start_row += scroll
            else:
                mbeep()

        if ch == ord(','):
            if start_row > 0:
                start_row -= scroll
            else:
                mbeep()

        if ch == cur.KEY_PPAGE:
            si = max(si - 10, 0)
            bmark = si
        elif ch == cur.KEY_NPAGE:
            si = min(si + 10, total_sents -1)
            bmark = si
        elif ch == cur.KEY_HOME:
            si = 0
            bmark = si
        elif ch == cur.KEY_END:
            si = total_sents -1 
            bmark = si

        if si < bmark:
            bmark = si

        if update_si:
            fc = max(fc, 0)
            fc = min(fc, total_frags-1)
            bmark = frags_sents[fc][0]
            si = frags_sents[fc+1][0]-1 if fc+1 < total_frags else total_sents - 1
        c = 0 
        while c < total_sects  and si >= art["sections"][c]["sents_offset"]:
            c += 1
        sc = max(c - 1,0)
        f = 0
        while f < total_frags and si >= frags_sents[f][0]:
            f += 1
        fc = max(f - 1,0)

        art['sections'][sc]['fc'] = fc 
        if ch == ord(':'):
            _comment,_ = minput(win_info, 0, 1, ":", default = comments[si]) 
            show_info(main_info)
            _comment = _comment if _comment != "<ESC>" else comments[si]
            art_changed = True
            if nods[si] == "" or nods[si] == "next":
                nods[si] = "okay"
                bmark = si
            comments[si] = _comment

        if ch == ord('t'):
            subwins = {
                    "select tag":{"x":7,"y":5,"h":15,"w":68}
                    }
            choice = ''
            mi = 0
            tags_menu = {"tags (comma separated)":"", "select tag":""} 
            tags_options = {}
            cur_tags = load_obj("tags","", [""])
            tags_options["select tag"] = cur_tags
            while choice != 'q':
                tags = ""
                if "tags" in art:
                    for tag in art["tags"]:
                        tags += tag + ", "
                tags_menu["tags (comma separated)"] = tags
                choice, tags_menu,mi = show_menu(tags_menu, tags_options,
                        shortkeys={"s":"select tag"},
                        subwins=subwins, mi=mi, title="tags")
                if choice == "select tag":
                    new_tag = tags_menu["select tag"].strip()
                    if not "tags" in art:
                        art["tags"] = [new_tag]
                    elif not new_tag in art["tags"]:
                        art["tags"].append(new_tag)
                else:
                    new_tags = tags_menu["tags (comma separated)"].split(",")
                    art["tags"]=[]
                    for tag in new_tags:
                        tag = tag.strip()
                        if tag != '' and not tag in art["tags"]:
                            art["tags"].append(tag)
                    if len(art["tags"]) > 0:
                        insert_article(saved_articles, art)
                    else:
                        remove_article(saved_articles, art)

                    save_obj(saved_articles, "saved_articles", "articles")
            text_win.erase()
            text_win.refresh(0,0, 2,0, rows -2, cols -1)
        if ch == ord('f'): # show figures
            ypos = 5
            fig_win = cur.newwin(8, width, ypos + 2, left)
            fig_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
            fig_win.border()
            opts = []
            fig_num =1
            for fig in figures:
                fig_num +=1
                caption = fig["caption"]
                if not caption.startswith("Figure"):
                   caption = "Figure " + str(fig_num) + ":" + caption
                opts.append(caption)

            fi = select_box(fig_win, opts, fi, in_row = False)
            if fi >= 0:
                fname = app_path + "/nodreader_temp.html" 
                if not figures_created:
                    create_figures_file(figures, fname)
                    figures_created = True
                webbrowser.open("file://" + fname + "#fig" + str(fi))
        if ch == ord('m'):
            choice = '' 
            while choice != 'q':
                choice, theme_menu,_ = show_menu(theme_menu, theme_options, title="theme")
            save_obj(theme_menu, conf["theme"], "theme")
            text_win.erase()
            text_win.refresh(0,0, 2,0, rows -2, cols-1)
        if ch == ord('q') or ch == 127: # before exiting artilce
            art["nods"] = nods
            art["times"] = rtime
            art["passable"] = passable
            art["comments"] = comments
            if show_nod == "":
                art["visible"] = visible
            if art_changed:
                insert_article(saved_articles, art)
                save_obj(saved_articles, "saved_articles", "articles")
            last_visited = load_obj("last_visited", "articles", [])
            insert_article(last_visited, art)
            save_obj(last_visited, "last_visited", "articles")
    return "" 

def create_figures_file(figures, fname):
    html = """
        <html>
        <head>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                }
                .caption {
                    font-size:24px;
                    font-weight:400;
                    line-height:28px;
                    padding:2% 10% 10% 10%;
                }
                .imgbox {
                    display: grid;
                    height:75%;
                    margin:2% 10% 2% 10%;
                }
                .center-fit {
                    max-width: 100%;
                    max-height: 100vh;
                    margin: auto;
                }
            </style>
        </head>
        <body>
    """
    for fnum, fig in enumerate(figures):
       url = fig["id"]
       if not url.startswith("http"):
           url = "https://dimsum.eu-gb.containers.appdomain.cloud/api/media/" + url
       caption = fig["caption"]
       html += """
            <div class="imgbox" id='fig""" + str(fnum) +  """'>
                <img class="center-fit" src='""" + url + """'>
            </div>
            <div class="caption">""" + caption + """</div>
       """
    html += "</body></html>"    
    with open(fname, "w", encoding="utf-8") as f:
         f.write(html)


def refresh_menu(menu, menu_win, sel, options, shortkeys, subwins):
    global clG
    menu_win.erase()
    mprint("", menu_win)
    mprint(" "*5 + "NodReader v 1.0", menu_win)
    row = 3 
    col = 5
    rows, cols = menu_win.getmaxyx() 
    _m = max([len(x) for x in menu.keys()]) + 5  
    gap = col + _m
    for k, v in menu.items():
       colon = ":" # if not k in options else ">"
       key = k
       if k in shortkeys.values():
           sk = list(shortkeys.keys())[list(shortkeys.values()).index(k)]
           key = sk + ") " + k
       if k == sel and not sel in subwins:
           color = CUR_ITEM_COLOR
       else:
           color = ITEM_COLOR
       fw = cur.A_BOLD
       if str(v) == "button_light":
           fw = None

       if k.startswith("sep"):
           if v:
             print_there(row, col,  str(v) + colon, menu_win, color)
       else:
           print_there(row, col, "{:<{}}".format(key, _m), menu_win, color, attr = fw)
           if not str(v).startswith("button") and not k in subwins:
             print_there(row, gap, colon, menu_win, color, attr = cur.A_BOLD)

       if not str(v).startswith("button") and not k in subwins:
           if "color" in k:
               print_there(row, col + _m + 2, "{:^5}".format(str(v)), menu_win, color_map[k]) 
           elif not k.startswith("sep"):
               tv = v
               lim = cols - (col + _m) - 10  
               if len(v) > lim:
                   tv = v[: lim] + "..."
               print_there(row, col + _m + 2, "{}".format(tv), menu_win, TEXT_COLOR)

       row += 1
    rows, cols = std.getmaxyx()
    menu_win.refresh(0,0, 0,0, rows-2, cols-1)
    for k, item in subwins.items():
       sub_menu_win = cur.newwin(item["h"],
                item["w"],
                item["y"],
                item["x"])
       sub_menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
       show_submenu(sub_menu_win, options[k],-1, "color" in k)

def get_sel(menu, mi):
    mi = max(mi, 0)
    mi = min(mi, len(menu)-1)
    return list(menu)[mi], mi

win_info = None
def show_info(msg, color=INFO_COLOR, bottom = True):
    global win_info
    rows, cols = std.getmaxyx()
    if bottom:
        win_info = cur.newwin(1, cols, rows-1,0) 
    else:
        win_info = cur.newpad(rows*2, 2*cols // 3)
    win_info.bkgd(' ', cur.color_pair(color)) # | cur.A_REVERSE)
    win_info.erase()
    if bottom:
        if len(msg) > cols - 15:
            msg = msg[:(cols - 16)] + "..."
        print_there(0,1," {} ".format(msg), win_info, color)
        win_info.clrtoeol()
        win_info.refresh()
    else:
        left = cols//6
        start_row = 0
        ch = 0
        guide = "\n  Press q to return"
        nlines = msg.count('\n')
        if nlines > rows - 5:
            guide += "; Press down and up keys to see the complete message"
        msg = guide + "\n" + msg
        while ch != ord('q'):
            win_info.erase()
            # msg = textwrap.indent(textwrap.fill(msg),'  ')
            mprint(msg, win_info, color)
            start_row = max(start_row, 0)
            start_row = min(start_row, 2*rows)
            win_info.refresh(start_row,0, 2,left, rows -3, cols-1)
            ch = get_key(std)
            if ch == cur.KEY_UP:
                if start_row > 0:
                    start_row -= 10
                else:
                    mbeep()
            elif ch == cur.KEY_DOWN:
                if start_row < nlines - rows + 5:
                    start_row += 10
                else:
                    mbeep()
            elif ch != ord('q'):
                mbeep()

def show_msg(msg, color=MSG_COLOR):
   mbeep()
   show_info(msg + " press any key", color)
   std.getch()

def show_err(msg, color=ERR_COLOR, bottom = True):
    show_info(msg+ " press any key...", color, bottom)
    if not bottom:
        std.getch()

def load_preset(new_preset, options, folder=""):
    menu = load_obj(new_preset, folder)
    if menu == None and folder == "theme":
        dark ={'preset': 'dark',"sep1":"colors", 'text-color': '247', 'back-color': '-1', 'item-color': '71', 'cur-item-color': '236', 'sel-item-color': '33', 'title-color': '28', "sep2":"reading mode","faint-color":'241' ,"highlight-color":'238', "inverse-highlight":"True", "bold-highlight":"False"}
        light = {'preset': 'light',"sep1":"colors", 'text-color': '233', 'back-color': '250', 'item-color': '22', 'cur-item-color': '24', 'sel-item-color': '25', 'title-color': '17', "sep2":"reading mode","faint-color":'239' ,"highlight-color":'24', "inverse-highlight":"True","bold-highlight":"False"}
        for mm in [dark, light]:
           mm["save as"] = "button"
           mm["reset"] = "button"
           mm["delete"] = "button"
           mm["save and quit"] = "button"
        save_obj(dark, "dark", "theme")
        save_obj(light, "light", "theme")
        new_preset = "dark"

    if menu == None and folder == "template":
       text  = {"preset":"txt", "top":"", "title":"# {title}", "section-title":"## {section-title}","paragraph": "{paragraph}{newline}{newline}", "bottom":"{url}"}
       html  = {"preset":"html", "top":"<!DOCTYPE html>{newline}<html>{newline}<body>","title":"<h1>{title}</h1>", "section-title":"<h2>{section-title}</h2>","paragraph": "<p>{paragraph}</p>", "bottom":"<p>source:{url}</p></body>{newline}</html>"}
       for mm in [text, html]:
           mm["save as"] = "button"
           mm["reset"] = "button"
           mm["delete"] = "button"
           mm["save and quit"] = "button"
       save_obj(text, "txt", folder)
       save_obj(html, "html", folder)
       new_preset = "txt"

    menu = load_obj(new_preset, folder)
    menu["preset"] = new_preset
    menu_dir = user_data_dir(appname, appauthor) + "/"+ folder
    saved_presets =  [Path(f).stem for f in Path(menu_dir).glob('*') if f.is_file()]
    options["preset"] = saved_presets

    if folder == "theme":
        reset_colors(menu)
    conf[folder] = new_preset
    save_obj(conf, "conf", "")
    return menu, options

def select_box(win, in_opts, ni, in_row = False, stack_index = 0):
    ch = 0
    win.border()
    opts = []
    for i,k in enumerate(in_opts[stack_index]):
        opts.append(str(i) + ") " + k)
    row_cap = 3 if in_row else 1
    while ch != 27 and ch != ord('q'):
        ni = max(ni, 0)
        ni = min(ni, len(opts)-1)
        win.erase()
        if not in_row:
            show_submenu(win, opts, ni, color = INFO_COLOR)
        else:
            for i,k in enumerate(opts):
                row = (i // row_cap) 
                col = (i % row_cap)*20
                if i == ni:
                    print_there(row, col, k, win, CUR_ITEM_COLOR)
                else:
                   print_there(row, col, k, win, INFO_COLOR)
            win.refresh()
        ch = get_key(std)
        if ch == cur.KEY_ENTER or ch == 10 or ch == 13:
           return ni, stack_index
        if chr(ch).isdigit():
            ni = int(chr(ch))
        elif ch == ord('d'):
            opts.pop(ni)
        elif ch == cur.KEY_DOWN:
            ni += row_cap
        elif ch == cur.KEY_UP:
            if ni < row_cap:
                return -1, stack_index
            ni -= row_cap
        elif ch == cur.KEY_RIGHT:
            ni += 1
        elif ch == cur.KEY_LEFT:
            if ni == 0: 
               if stack_index < len(in_opts) - 1:
                   stack_index += 1
                   nn, stack_index = select_box(win, in_opts, ni, in_row, stack_index)
                   if nn >= 0:
                       return nn, stack_index
               else:
                   return -1, stack_index
            else:
               ni -= 1
        elif ch != 27 and ch != ord('q'):
            mbeep()
            show_info("Use left arrow key to select the item, the right key or q to cancel!")

    return -1, stack_index
    

def show_submenu(sub_menu_win, opts, si, is_color = False, color = ITEM_COLOR):
   win_rows, win_cols = sub_menu_win.getmaxyx()
   win_rows = min(win_rows-3, 10)
   start = si - win_rows // 2
   start = max(start, 0)
   if len(opts) > win_rows:
 	  start = min(start, len(opts)-win_rows)
   if start > 0:
 	  mprint("...", sub_menu_win, color)
   footer = ""
   for vi, v in enumerate(opts[start:start + win_rows]):
     if start + vi == si:
        sel_v = v
        if len(v) > win_cols:
           footer = v
           v = v[:win_cols - 5] + "..."
        if is_color:
           mprint(" {:^8}".format(">" + str(v)), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
           mprint(" {:<8}".format(str(v)),sub_menu_win, CUR_ITEM_COLOR)
     else:
        if len(v) > win_cols:
           v = v[:win_cols - 5] + "..."
        if is_color:
           mprint(" {:^8}".format(v), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
           mprint(" {:<8}".format(str(v)), sub_menu_win, color)
   if start + win_rows < len(opts):
 	  mprint("...", sub_menu_win, color)
   # if footer != "":
   #   mprint(footer, sub_menu_win, cW)
   sub_menu_win.refresh()

menu_win = None
common_subwin = None
def show_menu(menu, options, shortkeys={}, title = "", mi = 0, subwins={}, info = "h) help | q) quit"):
    global menu_win, common_subwin

    si = 0 #submenu index
    ch = 0 #user choice
    mode = 'm' # 'm' means we are in menu, 's' means we are in submenu

    rows, cols = std.getmaxyx()
    height = rows - 1  
    width = cols  

    menu_win = cur.newpad(rows*2, cols)
    common_subwin = cur.newwin(rows - 6, width//2 + 5, 5, width//2 - 5)

    menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    common_subwin.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)

    if info.startswith("error"):
        show_err(info)
    else:
        show_info(info)

    mprint(title.center(rows), menu_win)
    hide_cursor()
    last_preset = ""
    if "preset" in menu:
        last_preset = menu["preset"]
        shortkeys["r"] = "reset"
        shortkeys["s"] = "save as"
        shortkeys["d"] = "delete"
        shortkeys["q"] = "save and quit"

    row = 3 
    col = 5
    mt, st = "", ""
    old_val = ""
    prev_ch = 0
    while ch != ord('q'):
        sel,mi = get_sel(menu, mi)
        sub_menu_win = common_subwin
        key_set = False
        cmd = ""
        if not sel.startswith("sep"):
            sub_menu_win.erase()
            if mode == 'm':
                refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
        if sel not in options and not str(menu[sel]).startswith("button") and not sel.startswith("sep"): 
             # menu[sel]=""
            cur_val = menu[sel]
            #refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
            _m = max([len(x) for x in menu.keys()]) + 5  
            win_input = cur.newwin(1, cols-10, row + mi, col)
            win_input.bkgd(' ', cur.color_pair(CUR_ITEM_COLOR)) # | cur.A_REVERSE)
            val, ch = minput(win_input,0, 0, "{:<{}}".format(sel,_m) + ": ", default=menu[sel]) 
            if val != "<ESC>":
                 val = textwrap.fill(val, width = cols - 12 - _m)
                 menu[sel] = val
                 if "tags" in sel and val.strip() != "":
                     new_tags = val.split(",")
                     new_tags = filter(None, new_tags)
                     for tag in new_tags:
                         tag = tag.strip()
                         if tag != '' and not tag in options["select tag"]:
                             options["select tag"].append(tag)
                     save_obj(options["select tag"],"tags","")
            else:
                 menu[sel] = cur_val
                 ch = ord('q')


            key_set = True
            if ch != cur.KEY_UP and ch != 27:
                 ch = cur.KEY_DOWN
            
            mode = 'm'
            mt = ""
        if sel in subwins:
            if mode == 'm' and menu[sel] in options[sel]:
               si = options[sel].index(menu[sel])
            mode = 's'
            rows, cols = std.getmaxyx() 
            sub_menu_win = cur.newwin(subwins[sel]["h"],
                subwins[sel]["w"],
                subwins[sel]["y"],
                subwins[sel]["x"])
            sub_menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
        if mode == 's' and not str(menu[sel]).startswith("button"):
            if sel in options:
              si = min(si, len(options[sel]) - 1)
              si = max(si, 0)
              show_submenu(sub_menu_win, options[sel], si, "color" in sel)

        if not sel.startswith('sep') and not key_set:
            prev_ch = ch
            ch = get_key(std)
        elif sel.startswith('sep') and mi == 0:
            ch = cur.KEY_DOWN
        elif sel.startswith('sep') and mi == len(menu) -1:
            ch = cur.KEY_UP
            
        if ch == cur.KEY_RESIZE:
            mbeep()
            refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)

        if ch == cur.KEY_DOWN:
            if mode == "m":
                mi += 1
            elif sel in options:
                si += 1
        elif ch == cur.KEY_UP:
            if sel in subwins and si == 0:
                mode = "m"
            if mode == "m":
                mi -= 1
            elif sel in options:
                si -= 1
        elif ch == cur.KEY_NPAGE:
            if mode == "m":
                mi += 10
            elif sel in options:
                si += 10
        elif ch == cur.KEY_PPAGE:
            if mode == "m":
                mi -= 10
            elif sel in options:
                si -= 10
        elif  ch == cur.KEY_ENTER or ch == 10 or ch == 13 or (chr(ch) in shortkeys and ch == prev_ch):
            is_button = str(menu[sel]).startswith("button")
            if is_button: 
              if sel == "save as" or sel == "reset" or sel == "delete" or sel == "save and quit":
                  cmd = sel
              else:
                  return sel, menu, mi 
            elif sel in options:
                si = min(si, len(options[sel]) - 1)
                si = max(si, 0)
            elif sel.startswith("sep"):
                mi += 1
            if mode == 'm' and not is_button:
                old_val = menu[sel]
                mode = 's'
                st = ""
                if sel in options and menu[sel] in options[sel]:
                    si = options[sel].index(menu[sel])
            elif mode == 's' and not is_button:
                if last_preset.strip() != "":
                    save_obj(menu, last_preset, title)
                menu[sel] = options[sel][si]
                #if "preset" in menu and title == "theme":
                #    reset_colors(menu)
                if sel == "preset":
                    new_preset = menu[sel]
                    menu,options = load_preset(new_preset, options, title)
                    last_preset = new_preset
                    refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
                    show_info(new_preset +  " was loaded")
                if sel in shortkeys.values():
                    return sel, menu, mi
                mode = 'm'    
                mt = ""
                si = 0
                old_val = ""
        elif ch == cur.KEY_RIGHT:
            if not str(menu[sel]).startswith("button"):
                old_val = menu[sel]
                if sel in options and menu[sel] in options[sel]:
                    si = options[sel].index(menu[sel]) 
                mode = 's'
                st = ""
        elif ch == cur.KEY_LEFT or ch == 27:
            if old_val != "":
                menu[sel] = old_val
                #refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
                #if "color" in sel:
                #    reset_colors(menu)
            old_val = ""
            mode = 'm'
            mt = ""
        if cmd == "save and quit":
            ch = ord('q')
        elif ch == ord('d') or cmd == "delete":
            if mode == 'm':
                item = menu[sel]
            else:
                item = options[sel][si]
            if not is_obj(item, title) and not sel == "preset":
                return "del@" + sel+"@" + str(si), menu, mi

            _confirm = confirm(win_info,  
                    "delete '" + item)

            if _confirm == "y" or _confirm == "a":
                show_info("Deleting '"+ item + "'")
                del_obj(item, title)
                if item in options[sel]:
                    options[sel].remove(item)
                if len(options[sel]) > 0:
                    new_item = options[sel][si] if si < len(options[sel]) else options[sel][0] 
                else:
                    new_item = "None"
                if sel == "preset":
                    menu,options = load_preset(new_item, options, title)
                    last_preset = menu["preset"]
                    si = options["preset"].index(menu["preset"]) 
                    refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
                    show_info(new_item +  " was loaded")
                else:
                    menu[sel] = new_item
                    show_info(item +  " was deleted")
                    return "del@" + sel+"@" + str(si), menu, mi

        elif (ch == ord('r') or cmd == "reset") and "preset" in menu:
            menu, options = load_preset("resett", options, title)
            last_preset = menu["preset"]
            #refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
            show_info("Values were reset to defaults")
        elif (ch == ord('s') or cmd == "save as") and "preset" in menu:
            fname,_ = minput(win_info, 0, 1, "Save as:") 
            if fname == "<ESC>":
                show_info("")
            else:
                save_obj(menu, fname, title)
                if title == "theme":
                    reset_colors(menu)
                show_info(menu["preset"] +  " was saved as " + fname)
                menu["preset"] = fname
                if not fname in options["preset"]:
                    options["preset"].append(fname)
                last_preset = fname
                refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
                mode = 'm'
        elif ch == ord('h'):
            return "h",menu, mi
        elif ch != ord('q') and chr(ch) in shortkeys:
            mi = list(menu.keys()).index(shortkeys[chr(ch)])
            sel,mi = get_sel(menu, mi)
            #refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
            if str(menu[sel]).startswith("button"):
                return sel, menu, mi
            old_val = menu[sel]
            mode = 's'
            st = ""
        else:
            if mode == 's' and chr(ch).isdigit() and sel in options:
                si,st = find(options[sel], st, chr(ch), si)
    return chr(ch), menu, mi

def find(list, st, ch, default):
    str = st + ch
    for i, item in enumerate(list):
        if item.startswith(str):
            return i,str
    for i, item in enumerate(list):
        if item.startswith(ch):
            return i,ch
    return default,""

def start(stdscr):
    global template_menu, template_options, theme_options, theme_menu, std, conf, query, filters

    std = stdscr
    logging.info(f"curses colors: {cur.COLORS}")

    # mouse = cur.mousemask(cur.ALL_MOUSE_EVENTS)
    cur.start_color()
    cur.curs_set(0) 
    # std.keypad(1)
    cur.use_default_colors()
    # sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=24, cols=112))
    rows, cols = std.getmaxyx()
    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    menu =  None #load_obj("main_menu", "")
    isFirst = False
    if menu is None or (newspaper_imported and not "webpage" in menu):
        isFirst = True
        menu = {}
        menu["reviewed articles"]="button"
        menu["sep1"] ="Search AI-related papers"
        menu["keywords"]=""
        menu["Go!"]="button"
        menu["advanced search"]="button"
        if newspaper_imported:
            menu["sep2"] = "Load website articles"
            menu["website articles"]="button"
            menu["webpage"]="button"
        menu["saved items"]= "button"
        menu["options"]="button"
        menu["text files"]="button"

    options = {
            "saved articles":["None"],
            "recent articles":["None"],
            }

    last_visited = load_obj("last_visited", "articles", [])
    recent_arts = []
    width = 2*cols//3
    y_start = len(menu) + 5
    for art in last_visited[:10]:
        recent_arts.append(art["title"][:60]+ "...")
    subwins = {}
    if recent_arts:
        menu["sep3"]=""
        menu["recent articles"] = ""
        options["recent articles"] =recent_arts 
        subwins = {"recent articles":{"x":7,"y":y_start,"h":6,"w":width}}

    if isFirst:
        for opt in menu:
           if opt in options:
               menu[opt] = options[opt][0] if options[opt] else ""

    conf = load_obj("conf", "")
    if conf is None:
        conf = {"theme":"default", "template":"txt"}

    colors = [str(y) for y in range(-1, cur.COLORS)]
    if cur.COLORS > 100:
        colors = [str(y) for y in range(-1, 100)] + [str(y) for y in range(112, cur.COLORS)]

    theme_options = {
            "preset":[],
            "text-color":colors,
            "back-color":colors,
            "item-color":colors,
            "cur-item-color":colors,
            "sel-item-color":colors,
            "title-color":colors,
            "highlight-color":colors,
            "faint-color":colors,
            "inverse-highlight":["True", "False"],
            "bold-highlight":["True", "False"],
            }

    theme_menu, theme_options = load_preset(conf["theme"], theme_options, "theme") 
    template_menu, template_options = load_preset(conf["template"], template_options, "template") 

    reset_colors(theme_menu)
    #os.environ.setdefault('ESCDELAY', '25')
    #ESCDELAY = 25
    std.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    clear_screen(std)
    ch = ''
    shortkeys = {"l":"reviewed articles", "n":"nods", "r":"recent articles","t":"tagged articles","o":"options", "p":"webpage", "a":"advanced search","s":"saved items", "w":"website articles",'t':"text files"}
    mi = 0
    while ch != 'q':
        info = "h) help         q) quit"
        show_info(info)
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi, subwins = subwins)
        save_obj(menu, "main_menu", "")
        if ch == "advanced search":
            search()
        elif ch == "last results":
            show_last_results()
        elif ch == 'l' or ch == "reviewed articles":
            saved_articles = load_obj("saved_articles","articles", [])
            rev_articles = []
            for art in saved_articles:
                if "nods" in art and art["nods"][0] != "":
                    rev_articles.append(art)
            if len(rev_articles) == 0:
                show_msg("There is no article reviewed yet, to review an article enter a nod for its title.")
            else:
                list_articles(rev_articles, "Reviewed Articles")

        elif ch == 's' or ch == "saved items":
            saved_items()
        elif ch == "Go!":
            query = menu["keywords"]
            fid = menu["keywords"]
            articles,ret = request(0)
            if len(articles) > 0 and ret == "":
                if isinstance(articles, tuple):
                    articles = articles[0]
                save_obj(articles, "last_results", "")
                ret = list_articles(articles, fid)
            if ret:
                show_err(ret[:200]+ "...", bottom = False)
        elif ch == "webpage":
            webpage()
        elif ch == 'o' or ch == "options":
            settings()
        if ch == 'h' or ch == "help":
            #webbrowser.open("https://github.com/puraminy/nodreader")
            show_info(('\n'
                       '      _   __          __   ____                 __\n'
                       '     / | / /___  ____/ /  / __ \___  ____ _____/ /__  _____\n'
                       '    /  |/ / __ \/ __  /  / /_/ / _ \/ __ `/ __  / _ \/ ___/\n'
                       '   / /|  / /_/ / /_/ /  / _, _/  __/ /_/ / /_/ /  __/ /\n'
                       '  /_/ |_/\____/\__,_/  /_/ |_|\___/\__,_/\__,_/\___/_/\n\n'
                       '  Please visit the following link to get an overview of Nodreader:\n'
                       '\thttps://github.com/puraminy/nodreader\n\n'
                       '\tArrow keys)   Next, previous item\n'
                       '\tEnter)        Open/Run the selected item\n'
                       '\tPageUp/Down)  First/Last item\n'
                       '\trrr           Resume reading from last article\n'
                       '\n  Further help was provided in each section.\n'),
                       bottom=False)
            #name = '../README.md'
            #with open(name, "r") as f:
            #    data = f.read()
            #title, i = get_title(data, name)
            #if i > 0:
            #    data = data[i:]
            #art = {"id":"help", "pdfUrl":name, "title":title, "sections":get_sects(data)}
            #show_article(art)
        elif ch == 'w' or ch == "website articles":
             website()
        elif ch == "r" or ch == "recent articles":
             si = options["recent articles"].index(menu["recent articles"]) 
             clear_screen(std)
             show_article(last_visited[si])
        elif ch == 'text files':
            save_folder = doc_path + '/txt'
            Path(save_folder).mkdir(parents=True, exist_ok=True)
            show_texts(save_folder)
        elif ch.startswith("del@recent articles"):
            parts = ch.split("@")
            last_visited.pop(int(parts[2]))
            save_obj(last_visited, "last_visited", "articles") 
        elif ch == 'o' or ch == "saved articles":
             selected = menu["saved articles"]
             if selected == None:
                 show_err("Please select articles to load")
             else:
                 articles = load_obj(selected, "articles")
                 if articles != None:
                     ret = list_articles(articles, "sel articles")
                 else:
                     show_err("Unable to load the file....")

def show_texts(save_folder):
    subfolders = [ f.name for f in os.scandir(save_folder) if f.is_dir() ]
    menu = {}
    for sf in subfolders:
        menu["[>] "+sf]="button"
    text_files =  [str(Path(f)) for f in Path(save_folder).glob('*.txt') if f.is_file()]
    if not text_files and not subfolders:
        menu[".."] = "button"
    count = 1
    for text in text_files:
        name = Path(text).name
        if len(name) > 60:
            name = name[:60] + "..."
        name = "[" + str(count) + "] " + name
        menu[name] = "button_light"
        count += 1
    options = {}
    mi = 0
    ch = ''
    while ch != 'q':
        ch, menu, mi = show_menu(menu, options, mi = mi)
        if ch.startswith("[>"):
            sfolder = save_folder + "/" + ch[4:]
            show_texts(sfolder)
        elif ch == "..":
            ch = 'q'
        elif ch != "q":
            index = mi - len(subfolders)
            text = text_files[index]
            with open(text, "r") as f:
                data = f.read()
            title, i = get_title(data, name)
            if i > 0:
                data = data[i:]
            art = {"id":text, "pdfUrl":name, "title":title, "sections":get_sects(data)}
            show_article(art) 

def saved_items():
    menu = {}
    #menu["reviewed articles"]="button"
    menu["tagged articles"]="button"
    menu["nods"]="button"
    menu["comments"]="button"
    shortkeys = {"s":"saved articles", "c":"comments", "n":"nods", "t":"tagged articles", 'x':"text files"}
    options = {}
    mi = 0
    ch = ''
    while ch != 'q':
        info = "h) help         q) quit"
        show_info(info)
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi)
        if ch == "n" or ch == "nods":
             list_notes("nods")
        elif ch == "c" or ch == "comments":
             list_comments()
        elif ch == 't' or ch == "tagged articles":
            list_tags()
        elif ch == 's' or ch == "saved articles":
            saved_articles = load_obj("saved_articles","articles")
            list_articles(saved_articles, "Saved Articles")
def settings():
    global theme_menu, doc_path
    choice = '' 
    menu = load_obj("options", "")
    font_size = 24
    path = '~/Documents/Nodreader'
    path.replace('/', os.sep)
    doc_path = os.path.expanduser(path)
    if menu is None:
        menu = {"theme":"button","documents folder":""}
        menu["documents folder"] = doc_path
    else:
        if os.name == 'nt':
            font_size = menu["font size"]
        doc_path = menu["documents folder"]

    if doc_path.endswith("/"):
        doc_path = doc_path[:-1]
    options = {}
    if os.name == 'nt':
        menu["font size"]=font_size
        options["font size"] = [str(fs) for fs in range(18, 26)]

    menu["save and quit"] = "button"
    mi = 0
    while choice != 'q':
        choice, menu, mi = show_menu(menu, options, title="options", shortkeys={"f": "font size","q":"save and quit"})  
        if choice == "theme":
            _, theme_menu,_ = show_menu(theme_menu, theme_options, title="theme")
            save_obj(theme_menu, conf["theme"], "theme")
        if choice == "font size":
            resize_font_on_windows(int(menu["font size"])) # std)
            show_msg("The font size will changes in the next run of the application")

    doc_path = menu["documents folder"]
    Path(doc_path).mkdir(parents=True, exist_ok=True)
    save_obj(menu, "options", "")
    

def list_notes(notes = "nods"):
    subwins = {
            notes:{"x":7,"y":5,"h":15,"w":68},
            }
    choice = ''
    opts, art_list = refresh_notes(notes)
    if not art_list:
        show_msg("There is no article with nods!")
        return
    clear_screen(std)
    mi = 0
    while choice != 'q':
        nods = ""
        menu = {notes:""} 
        choice, menu,mi = show_menu(menu, opts,
                shortkeys={"n":"nods", "c":"comments"},
                subwins=subwins, mi=mi, title=notes)
        if choice == notes:
            sel_nod = menu[notes][:-5]
            sel_nod = sel_nod.strip()
            articles = art_list[sel_nod]
            if len(articles) > 0:
                ret = list_articles(articles, sel_nod, True)
            opts, art_list = refresh_notes()

def list_comments():
    saved_articles = load_obj("saved_articles","articles", [])
    N = len(saved_articles)
    art_list = []
    for art in saved_articles:
        if "comments" in art:
            art_list.append(art)
    if len(art_list) > 0:
        ret = list_articles(art_list, "comments", True)
    else:
        show_msg("There is no article with comments!")
        return

def refresh_notes(note = "nods"):
    saved_articles = load_obj("saved_articles","articles", [])
    N = len(saved_articles)
    art_num = {}
    art_list = {}
    nod_list = []
    for art in saved_articles:
        if not note in art:
            continue
        art_nods = art[note]
        for nod in art_nods:
            nod = nod.strip()
            if nod == "okay" or nod == "next" or nod == "":
                continue
            if not nod in nod_list:
                nod_list.append(nod)
            if nod in art_num:
                art_num[nod] += 1
                if not art in art_list[nod]:
                    art_list[nod].append(art)
            else:
                art_num[nod] = 1
                art_list[nod] = [art]
    opts = {note:[]}
    for nod in nod_list:
        opts[note].append(nod.ljust(40) + str(art_num[nod]))
    return opts, art_list

def refresh_tags():
    saved_articles = load_obj("saved_articles","articles", [])
    N = len(saved_articles)
    art_num = {}
    art_list = {}
    tag_list = []
    for art in saved_articles:
        if not "tags" in art:
            continue
        for tag in art["tags"]:
            tag = tag.strip()
            if not tag in tag_list:
                tag_list.append(tag)
            if tag in art_num:
                art_num[tag] += 1
                if not art in art_list[tag]:
                    art_list[tag].append(art)
            else:
                art_num[tag] = 1
                art_list[tag] = [art]
    opts = {"tags":[]}
    for tag in tag_list:
        opts["tags"].append(tag.ljust(40) + str(art_num[tag]))
    save_obj(tag_list, "tags", "")
    return opts, art_list

def list_tags():
    subwins = {
            "tags":{"x":7,"y":5,"h":15,"w":68},
            }
    choice = ''
    opts, art_list = refresh_tags()
    if not art_list:
        show_msg("There is no tagged article!")
        return
    clear_screen(std)
    mi = 0
    while choice != 'q':
        tags = ""
        menu = {"tags":""} 
        choice, menu,mi = show_menu(menu, opts,
                shortkeys={"t":"tags"},
                subwins=subwins, mi=mi, title="tags")
        if choice == "tags":
            sel_tag = menu["tags"][:-5]
            sel_tag = sel_tag.strip()
            articles = art_list[sel_tag]
            if len(articles) > 0:
                ret = list_articles(articles, sel_tag, group = "tags")
            opts, art_list = refresh_tags()
        elif choice.startswith("del@tags"):
            save_obj(menu["tags"], "tags", "")

def website():

    menu = load_obj("website_menu", "")
    isFirst = False
    if menu is None:
        menu = {"address":"", "load":"button", "popular websites":"", "saved websites":""}
        isFirst = True

    shortkeys = {"l":"load", "p":"popular websites", 's':"saved websites"}
    ws_dir = user_data_dir(appname, appauthor) + "/websites"
    saved_websites =  [Path(f).stem for f in Path(ws_dir).glob('*') if f.is_file()]
#    if saved_websites:
#        menu["sep1"] = "saved websites"
#    c = 1 
#    for ws in reversed(saved_websites):
#        menu[ws] = "button"
#        shortkeys[str(c)] = ws
#        c += 1
    options = {"history":["None"], "bookmarks":["None"]}
    options["popular websites"] = newspaper.popular_urls()
    options["saved websites"] = saved_websites
    history = load_obj("history", "")
    if history is None:
        history = ["None"]
    elif "None" in history:
        history.remove("None")
    options["history"] = history
    if isFirst:
        for opt in menu:
           if opt in options:
               menu[opt] = options[opt][0] if options[opt] else ""
    clear_screen(std)
    ch = ''
    mi = 0
    subwins = {"saved websites":{"x":16,"y":7,"h":10,"w":48}}
    info = "h) help | q) quit"
    while ch != 'q':
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi, subwins= subwins, info = info)
        if (ch == "load" or ch == "l" or ch == "popular websites"):
            site_addr = ""
            if ch == 'l' or ch == "load":
                site_addr = menu["address"]
            if ch == "popular websites":
                site_addr = menu["popular websites"]
            if not site_addr:
                info = "error: the site address can't be empty!"
            else:
                 show_info("Gettign articles from " + site_addr  + "... | Hit Ctrl+C to cancel")
                 config = newspaper.Config()
                 config.memoize_articles = False
                 try:
                     site = newspaper.build(site_addr, memoize_articles = False) # config)
                     # logger.info(site.article_urls())
                     # site.download()
                     # site.generate_articles()
                 except Exception as e:
                     info = "error: " + str(e)
                     if ch == 'l' or ch == "load":
                         mi = 0
                     continue
                 except KeyboardInterrupt: 
                     show_info("loading canceled")
                     continue
                 if not site_addr in history:
                     history.append(site_addr)
                     save_obj(history, "history", "")
                 articles = []
                 stored_exception=None
                 for a in site.articles:
                     try:
                         a.download()
                         a.parse()
                         sleep(0.01)
                         show_info("loading "+ a.title[:60] + "...")
                         if stored_exception:
                            break
                     except KeyboardInterrupt:
                         stored_exception=sys.exc_info()
                     except Exception as e:
                         show_info("Error:" + str(e))
                         continue

                     #a.nlp()
                     figures = []
                     count = 0
                     for img in list(a.imgs):
                         count += 1
                         figures.append({"id":img, "caption": "Figure " + str(count)})
                     art = {"id":a.title,"pdfUrl":a.url, "title":a.title, "figures":figures, "sections":get_sects(a.text)}
                     articles.append(art)
                 if articles != []:
                     uri = urlparse(site_addr)
                     save_obj(articles, uri.netloc, "websites")
                     ret = list_articles(articles, site_addr)
                 else:
                     info = "error: No article was found or an error occured during getting articles..."
             
        if ch == "saved websites":
             selected = menu["saved websites"]
             if selected == "":
                 show_err("Please select articles to load")
             else:
                 articles = load_obj(selected, "websites")
                 if articles != None:
                     ret = list_articles(articles, "sel articles")
                 else:
                     show_err("Unable to load the file....")
    save_obj(menu, "website_menu", "")

def webpage():

    menu =  None #load_obj("webpage_menu", "")
    isFirst = False
    if menu is None:
        menu = {"address":"","sep1":"", "load":"button", "recent pages":""}
        isFirst = True

    shortkeys = {"l":"load", "r":"recent pages"}
    options = {}

    recent_pages = load_obj("recent_pages", "articles")
    if recent_pages is None:
        recent_pages = []
    arts = []
    for art in recent_pages:
        uri = urlparse(art["pdfUrl"])
        name = "(" + uri.netloc + ") " + art["title"]
        arts.append(name)
    options["recent pages"] = arts
    subwins = {"recent pages":{"x":12,"y":7,"h":10,"w":68}}
    if isFirst:
        for opt in menu:
           if opt in options:
               menu[opt] = options[opt][0] if options[opt] else ""

    menu["address"]=""
    clear_screen(std)
    ch = ''
    mi = 0
    history = load_obj("history", "", [])
    info = ""
    while ch != 'q':
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi, subwins= subwins, info = info)
        url = ""
        if ch == 'l' or ch == "load":
            url = menu["address"]
        if url != "":
             show_info("Gettign article from " + url)
             config = newspaper.Config()
             config.memoize_articles = False
             config.fetch_images = False
             config.follow_meta_refresh = True
             try:
                 a  = newspaper.Article(url)
                 a.download()
                 a.parse()
                 # site.generate_articles()
             except Exception as e:
                 info = "error: " + str(e)
                 if ch == 'l' or ch == "load":
                     mi = 0
                 continue
             except KeyboardInterrupt:
                 continue
             if not url in history:
                 history.append(url)
                 save_obj(history, "history", "")
             art = {"id":a.title,"pdfUrl":a.url, "title":a.title, "sections":get_sects(a.text)}
             insert_article(recent_pages, art)
             del recent_pages[100:]
             save_obj(recent_pages, "recent_pages","articles")
             show_article(art)
        elif ch == "recent pages":
             si = options["recent pages"].index(menu["recent pages"]) 
             show_article(recent_pages[si])
    save_obj(menu, "webpage_menu", "")

def search():
    global query, filters
    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    menu = None #load_obj("query_menu", "")
    isFirst = False
    if menu is None:
        isFirst = True 
        menu = {}
        if is_obj("last_results",""):
            menu["last results"]="button"
        menu["keywords"] = ""
        menu["year"] = ""
        menu["task"] =""
        menu["conference"] = ""
        menu["dataset"] = ""
        menu["sep1"] = ""
        menu["search"] = "button"
    options = {
            "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
            "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
            "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
            "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ],
            }
    if isFirst:
        for opt in menu:
           if opt in options:
               menu[opt] = options[opt][0] if options[opt] else ""
    clear_screen(std)
    ch = ''
    shortkeys = {"s":"search", "l":"last results"}
    mi = 0
    while ch != 'q':
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi)
        if ch != 'q':
            for k,v in menu.items():
                if k in filter_items and v and v != "All":
                    filters[k] = str(v)
            try:
                ret = ""
                if ch == 's' or  ch == 'search':
                    show_info("Getting articles...")
                    query = menu["keywords"]
                    fid = menu["keywords"] + '_' + menu["year"] + '_1_' + menu["conference"] + '_' + menu["task"] + '_' + menu["dataset"]
                    fid = fid.replace('','All')
                    fid = fid.replace('__','_')
                    fid = fid.replace('__','_')
                    fid = fid.replace('__','_')
                    articles,ret = request(0)
                    if len(articles) > 0 and ret == "":
                        if isinstance(articles, tuple):
                            articles = articles[0]
                        save_obj(articles, "last_results", "")
                        ret = list_articles(articles, fid)
                    if ret:
                        show_err(ret[:200]+ "...", bottom = False)

                elif ch == 'l' or ch == "last results":
                    show_last_results()

            except KeyboardInterrupt:
                choice = ord('q')
                show_cursor()
    save_obj(menu, "query_menu", "")

def show_last_results():
     menu = load_obj("query_menu", "", {"keywords":""})
     last_query = menu["keywords"]
     query = last_query
     last_results_file = user_data_dir(appname, appauthor) + "/last_results.pkl"
     obj_file = Path(last_results_file) 
     if  obj_file.is_file():
        cr_time = time.ctime(os.path.getmtime(last_results_file))
        cr_date = datetime.datetime.strptime(str(cr_time), "%a %b %d %H:%M:%S %Y")
     articles = load_obj("last_results", "", [])
     if articles:
         ret = list_articles(articles, "results at " + str(cr_date))
     else:
         show_msg("Last results is missing....")

def main():
    global doc_path
    nr_options = load_obj("options", "")
    if nr_options != None:
        doc_path = nr_options["documents folder"]
        Path(doc_path).mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        maximize_console(29)       
        orig_size = resize_font_on_windows(20, True)
        orig_size = int(orig_size) if str(orig_size).isdigit() else 20
        if nr_options != None:
            fsize =int(nr_options["font size"]) if "font size" in nr_options else 24 
            if fsize > 24:
                fsize = 24
            ret = resize_font_on_windows(fsize)
            if ret != "":
                logging.info(ret)
    wrapper(start)
    if os.name == "nt":
        ret = resize_font_on_windows(orig_size) 
        if ret != "":
            logging.info(ret)

if __name__ == "__main__":
    main()
