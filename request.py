import requests
from datetime import date
from tqdm import tqdm
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
import newspaper
import getch as gh
from utility import *
import _curses # _curses.pyd supplied locally for python27 win32
import curses as cur
from curses import wrapper
from curses.textpad import rectangle
from pathlib import Path
from urllib.parse import urlparse
from appdirs import *
import logging, sys
logging.basicConfig(filename='nodreader.log', level=logging.DEBUG)

appname = "NodReader"
appauthor = "App"

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
        "":(242,bcolors.HEADER),
        "OK":(36,bcolors.OKBLUE),
        "interesting!":(114,bcolors.OKGREEN),
        "didn't get":(218,bcolors.FAIL),
        "so?":(248,bcolors.WARNING),
        "how?":(179,bcolors.WARNING),
        "needs review":(179,bcolors.WARNING),
        "needs research":(179,bcolors.WARNING),
        "got it!":(98,bcolors.OKGREEN),
        }

cW = 7
cR = 1
cG = 4
cY = 5
cB = 6 
cPink = 15
cC = 8
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
    for each in range(cur.COLORS):
        cur.init_pair(each, each, bg)
    cur.init_pair(TEXT_COLOR, int(theme["text-color"]), bg)
    cur.init_pair(ITEM_COLOR, int(theme["item-color"]), bg)
    cur.init_pair(CUR_ITEM_COLOR, bg, int(theme["cur-item-color"]))
    cur.init_pair(SEL_ITEM_COLOR, int(theme["sel-item-color"]), bg)
    cur.init_pair(TITLE_COLOR, int(theme["title-color"]), bg)
    cur.init_pair(INFO_COLOR, bg, int(theme["text-color"]))
    if theme["inverse-highlight"] == "True":
        cur.init_pair(HL_COLOR, bg, int(theme["highlight-color"]))
    else:
        cur.init_pair(HL_COLOR, int(theme["highlight-color"]), bg)
    cur.init_pair(FAINT_COLOR, int(theme["faint-color"]), bg)
    cur.init_pair(ERR_COLOR, cW, cR)
    cur.init_pair(MSG_COLOR, cW, cC)
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
import subprocess, os, platform
    
def openFile(filepath):
    _file = Path(filepath)
    if _file.is_file(): 
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filepath))
    else:
        show_err(filepath + " doesn't exist, you can download it by hitting d key")

def download(url, title):
    show_info("Starting download ...")
    file_name = title.replace(' ','-')[:50] + ".pdf"#url.split('/')[-1]
    f,_  = minput(win_info, 0, 1, "Save articles as:", default = file_name) 
    if f != '<ESC>':
        file_name = f

    # Streaming, so we can iterate over the response.
    _file = Path(file_name)
    if _file.is_file(): 
        openFile(_file)
    else:
        response = requests.get(url, stream=True)
        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024*10 #10 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(file_name, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            show_err("ERROR, something went wrong")
        else:
            openFile(_file)

    #text = pdfparser(file_name)
    #text = text[:10000]
    #text = text.replace("\n\n","<stop>")
    #art = {"id":file_name, "pdfUrl":file_name, "title":file_name, "sections":[{"title":"all", "fragments":get_frags(text)}]}
    #show_article(art)


def save_obj(obj, name, directory):
    if name.strip() == "":
        logging.info("Empty object to save")
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
        for sect in sects:
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

def remove_tag(art, fid, tagged_articles):
    if "tags" in art:
        for i, tag in enumerate(art["tags"]):
            if tag == fid:
                art["tags"].pop(i)
                update_article(tagged_articles, art)
                save_obj(tagged_articles, "tagged_articles", "articles")
                break

def request(p = 0):
     
    global page

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

def list_articles(articles, fid, show_nod = False, group=""):
    global template_menu

    N = len(articles)
    if N <= 0:
        return "No result found!"
    rows, cols = std.getmaxyx()
    main_win = cur.newwin(rows-2, cols-5, 3, 5)
    width = cols - 10
    main_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    sel_arts = []
    tagged_articles = load_obj("tagged_articles", "articles", [])
    tags = load_obj("tags","")
    ch = 0
    start = 0
    k = 0
    while ch != ord('q'):
        clear_screen(std)
        main_win.clear()
        print_there(2, 5, fid + " " + query, std)
        for j,a in enumerate(articles[start:start + 15]): 
            i = start + j
            paper_title =  a['title']
            dots = ""
            if "year" in a:
                h = a['year']
            else:
                h = i
            if len(paper_title) > width - 10:
               dots = "..."
            item = "[{}] {}".format(h, paper_title[:width - 10] + dots)               
            color = ITEM_COLOR
            if a in sel_arts:
                color = SEL_ITEM_COLOR
            if i == k:
                color = CUR_ITEM_COLOR

            mprint(item, main_win, color)

        main_win.refresh()
        _p = k // 15
        all_pages = (N // 15) + (1 if N % 15 > 0 else 0) 
        show_info("Enter) view article       PageDown) next page (load more...)     h) other shortkeys")
        print_there(0, cols - 15, "|" + str(N) + "|" + str(_p + 1) +  " of " + str(all_pages), win_info, INFO_COLOR)
        ch = get_key(std)
        if ch == cur.KEY_ENTER or ch == 10:
            k = max(k, 0)
            k = min(k, N-1)
            if show_nod:
                show_article(articles[k], fid)
            else:
                show_article(articles[k])

        if ch == cur.KEY_UP:
            if k > 0:
                k -= 1
            else:
                cur.beep()
        if ch == cur.KEY_DOWN:
            if k < N -1:
                k +=1
            else:
                cur.beep()

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
                       ' t)          tag selected items\n'
                       ' d)          delete selected items from list\n'
                       ' w)          write selected items into file\n'
                       ' f)          select output file format\n'
                       ' m)          change color theme\n'
                       ' HOME)       go to the first item\n'
                       ' END)        go to the last item\n'
                       ' PageUp)     previous page\n'
                       ' Arrow keys) next, previous article\n'
                       ' q)          return back to the search menu\n'
                       '\n\n Press any key to close ...'),
                       bottom=False)
            win_info.getch()
        if  ch == ord('s'):
            if not articles[k] in sel_arts:
                sel_arts.append(articles[k])
            else:
                sel_arts.remove(articles[k])
        if ch == ord('a'):
            sel_arts = []
            for ss in range(start,min(N, start+15)):
                  art = articles[ss]
                  if not ss in sel_arts:
                      sel_arts.append(art)
                  else:
                      sel_arts.remove(art)
        if ch == ord('d') and group =="tags":
            if not sel_arts:
                art = articles[k]
                if len(art["tags"]) == 1:
                    _confirm = confirm(win_info, " remove the last tag of " + art["title"][:20])
                    if _confirm == "y" or _confirm == "a":
                        remove_tag(art, fid, tagged_articles)
                        articles.remove(art)
                else:
                    remove_tag(art, fid, tagged_articles)
                    articles.remove(art)
            else:
                _conf_all = False
                for art in sel_arts:
                    if len(art["tags"]) == 1 and not _conf_all:
                        _confirm = confirm(win_info, " remove the last tag of " + art["title"][:20])
                        _conf_all = _confirm == "a"
                        if _confirm == "y" or _confirm == "a":
                            remove_tag(art, fid, tagged_articles)
                            articles.remove(art)
                    else:
                        remove_tag(art, fid, tagged_articles)
                        articles.remove(art)
                sel_arts = []
            N = len(articles)
            k = 0

        if ch == ord('f'):
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
                        insert_article(tagged_articles, a)
                        save_obj(tagged_articles, "tagged_articles", "articles")
                        show_info("Selected articles were added to tagged articles ")
                    sel_arts = []
        if ch == ord('w'): 
            if not sel_arts:
                show_err("No article was selected!! Select an article using s")
            else:
                fid,_ = minput(win_info, 0, 1," Folder name:", default = fid) 
                for a in sel_arts: 
                    write_article(a, fid)
                show_msg(str(len(sel_arts))+ " articles were downloaded and saved into:" + fid)
                sel_arts = []

def replace_template(template, old_val, new_val):
    ret = template.replace("{newline}","\n")
    ret = ret.replace(old_val,new_val)
    return ret

def write_article(article, folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    top = replace_template(template_menu["top"],"{url}", article["pdfUrl"])
    bottom = replace_template(template_menu["bottom"],"{url}", article["pdfUrl"])
    paper_title = article['title']
    file_name = paper_title.replace(' ','_').lower()
    ext = '.' + template_menu["preset"]
    fpath = folder + '/' + file_name + ext
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

def show_article(art, show_nod=""):
    global theme_menu, theme_options, query, filters
    rows, cols = std.getmaxyx()
    sects_num = 0
    sel_sects = {}
    sel_arts = []
    k,sc  = 0,0
    fast_read = False
    show_prev = False
    break_to_sent = False 
    start_row = 0
    width = 2*cols // 3 
    text_win = cur.newpad(rows*50, width)
    main_win = cur.newwin(rows, cols, 0, 0)
    text_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    main_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)

    # text_win = std
    bg = ""
    tagged_articles = load_obj("tagged_articles", "articles", [])
    nod_articles = load_obj("nod_articles", "articles", [])
    expand = 3
    frags_text = ""
    art_id = -1
    si = 0
    bmark = 0
    fc = 1
    cury = 0
    page_height = rows - 4
    scroll = 1
    show_reading_time = False
    start_reading = True
    cur_sent = "1"
    is_section = False
    art_id = art['id']
    
    sc = 0
    fc = 1
    si = 0
    frags_sents = {}
    frags_sents[0] = (0, art["title"])
    fsn = 1
    ffn = 1
    for b in art["sections"]:
        frags_text = ""
        b['frags_offset'] = ffn
        b["sents_offset"] = fsn
        frags_sents[ffn] = (fsn, b["title"])
        ffn += 1
        fsn += 1
        for c in b['fragments']:
            text = c['text']
            # if text.strip() != "":
            sents = split_into_sentences(text)
            frags_sents[ffn] = (fsn, sents)
            c['sents_offset'] = fsn 
            c['sents_num'] = len(sents)
            fsn += len(sents)
            ffn += 1
        b["sents_num"] = fsn - b["sents_offset"]
        b['frags_num'] = len(b["fragments"])
    total_sents = fsn 
    total_frags = ffn
    if si >= total_sents -1:
        si = 0


    ch = 0
    HL_COLOR = SEL_ITEM_COLOR
    ni = 0
    show_all = False
    if "visible" in art:
        visible = art["visible"]
    else:
        visible = [True]*total_sents
    if "passable" in art:
        passable = art["passable"]
    else:
        passable = [False]*total_sents
    if "nods" in art:
       nod = art["nods"]
    else:
       nod = [""]*total_sents
    if "times" in art:
       rtime = art["times"]
    else:
       rtime = {} 
    pos = [0]*total_sents
    nods_changed = False
    show_info("r) resume from last position")
    figures = []
    if "figures" in art:
        figures = art["figures"]
    while ch != ord('q') and ch != 127:
        # clear_screen(text_win)
        start_row = max(0, start_row)
        start_row = min(cury - 1, start_row)
        if bg != theme_menu["back-color"]:
            clear_screen(main_win)
            bg = theme_menu["back-color"]
            text_win.refresh(start_row,0, 0,0, rows-1, cols)
        start_time = time.time()
        text_win.clear()
        sn = 0
        sects_num = len(art["sections"])
        sc = max(sc, 0)
        sc = min(sc, sects_num)
        title = "\n".join(textwrap.wrap(art["title"], width)) # wrap at 60 characters
        pdfurl = art["pdfUrl"]
        top =  "["+str(k)+"] " + title 
        if si == 0:
            mprint(top,  text_win, HL_COLOR, attr = cur.A_BOLD) 
            cur_sent = top
        else:
            mprint(top,  text_win, TITLE_COLOR, attr = cur.A_BOLD) 
        mprint(pdfurl,  text_win, TITLE_COLOR, attr = cur.A_BOLD) 
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
 
            if sect_title != "all":
                mprint(sect_title, text_win, _color, attr = cur.A_BOLD)
#            if "figure" in b and b["figure"] is not None:
#                fig_num = int(b["figure"])
#                fig = figures[fig_num]
#                mprint("Figure " + str(fig_num), text_win, _color, attr = cur.A_BOLD)

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
                               nod[fsn] = "" if nod[fsn] == "okay?" else nod[fsn]
                                   # sent += f_color + " [" + feedback + "]" + f_color
                               
                               feedback = nod[fsn] 
                               if show_nod != "" and show_nod != feedback and not show_all:
                                   visible[fsn] = False

                               if not visible[fsn]: 
                                   pos[fsn],_ = text_win.getyx()
                                   fsn +=1 
                                   continue

                               #cur.init_pair(NOD_COLOR,back_color,cG)
                               reading_time = rtime[fsn][1] if fsn in rtime else 0 
                               f_color = SEL_ITEM_COLOR
                               hline = "-"*(width)
                               # f_color = nod_color[feedback]
                               #if feedback == "":
                               #else:
                               #    color = TEXT_COLOR # nod_color[feedback]
                               if show_reading_time:
                                   f_color = scale_color(reading_time)
                                   mprint(str(reading_time), text_win, f_color)
                               lines = textwrap.wrap(sent, width-2) 
                               lines = filter(None, lines)
                               end = ""
                               sent = ""
                               for line in lines:
                                   sent += line.ljust(width-2)+"\n" 
                               if fsn >= bmark and fsn <= si:
                                   hl_pos = text_win.getyx() 
                                   cur_sent = sent
                                   #if fsn < si:
                                   hlcolor = CUR_ITEM_COLOR
                                   #else:
                                   #   hlcolor = HL_COLOR
                                      # mprint(hline, text_win, hlcolor, end="")
                                   if theme_menu["bold-highlight"]== "True":
                                       mprint(sent, text_win, hlcolor, attr=cur.A_BOLD, end=end)
                                   else:
                                       mprint(sent, text_win, hlcolor, end=end)
                                   # mprint(hline, text_win, hlcolor, end="")
                               else:
                                   mprint(sent, text_win, color, end=end)
                               if feedback != '' and feedback != 'OK' and passable[fsn] == False:
                                   if feedback == 'yes':
                                       feedback = u'\u2713'
                                   f_color,_ = nod_color[feedback]
                                   mprint(feedback, text_win, f_color, end = "\n")
                                   # mprint("\n" + hline, text_win, FAINT_COLOR)
                                   # mprint(feedback, text_win, f_color, end="\n")
                                   # mprint(hline, text_win, FAINT_COLOR, end="")
                                   # start_row += 1
                               else:
                                   pass # mprint("", text_win, f_color)
                               pos[fsn],_ = text_win.getyx()
                               fsn += 1
                       
                       mprint("", text_win, color)
                       ffn += 1
                     # end for fragments
            sn += 1
         # end for sections
 
        #print(":", end="", flush=True)
        cury, curx = text_win.getyx()
        sc = min(sc, sects_num)
        f_offset = art['sections'][sc]['frags_offset'] 
        offset = art["sections"][sc]["sents_offset"] 
        # show_info("frags:"+ str(total_frags) + " start row:" + str(start_row) + " frag offset:"+ str(f_offset)  + " fc:" + str(fc) + " si:" + str(si) + " sent offset:" + str(offset))
        if not (ch == ord('.') or ch == ord(',')): 
            if pos[bmark] > 7:    
                start_row = pos[bmark] - 7 
            else:
                start_row = 0

        left = (cols - width)//2
        #if ch != cur.KEY_LEFT:
        text_win.refresh(start_row,0, 2,left, rows -2, cols)
        ch = get_key(std)
        show_info("r) resume from last position")
        if ch == ord('+'):
            if width < 2*cols // 3: 
                text_win.clear()
                text_win.refresh(0,0, 2,0, rows -2, cols)
                width +=2
            else:
                cur.beep()
        if ch == ord('-'):
            if width > cols // 3:
                text_win.clear()
                text_win.refresh(0,0, 2,0, rows -2, cols)
                width -= 2
            else:
               cur.beep()
        if ch == ord('d'):
            download(art["pdfUrl"], art["title"])
        if ch == ord('u'):
            with open(art["title"]  + ".txt","w") as f:
                print(art, file = f)
        if ch == ord('r'):
           cur.beep()
           if nod:
               si = 0
               while nod[si] != "" or visible[si] == False:
                   si += 1
               si = min(si, total_sents - 1)
               bmark = si

        if ch == ord('v'):
            start_reading = not start_reading
        if ch == ord('z'):
            show_reading_time = not show_reading_time

        if ch == ord('x'):
            fast_read = not fast_read
        if ch == ord('a'):
            if not art in sel_arts:
                sel_arts.append(art)

        if ch == ord('w'):
            folder = "articles-" + date.today().strftime('%Y-%m-%d')
            write_article(art, folder)
            show_msg("The article was written in " + folder)
        if ch == ord('y'):
            _confirm = confirm(win_info, "reset the article")
            if _confirm == "y" or _confirm == "a":
                nod = [""]*total_sents
                rtime = {} 
                visible = [True]*total_sents
                passable = [False]*total_sents
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
            nod_set = False
            _nod = nod[si] 
            if ch == cur.KEY_RIGHT:
                if _nod == "":
                    _nod = "OK"
            elif ch == cur.KEY_LEFT:
                ypos = pos[bmark]-start_row
                nod_win = cur.newwin(8, 15, ypos + 2, left - 2)
                nod_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
                opts = ["interesting!", "so?", "how?","needs review", "needs research", "didn't get", "got it!", "remove"]
                ni = select_box(nod_win, opts, ni)
                if ni >= 0:
                    _nod = opts[ni]
                    nod_set = True
                    nods_changed = True
#            
            for ii in range(bmark, si + 1):
                #if ii < si:
                #    passable[ii] = True
                if _nod == "remove":
                    visible[ii] = False
                if visible[si] and (nod[ii] == "" or nod[ii] == "OK"):
                    nod[ii] = _nod

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
            next_sect_start = total_sents
            if sc + 1 < sects_num:
                next_sect_start = art["sections"][sc +1]["sents_offset"]
            if ch == cur.KEY_DOWN and (si + 1 >= next_sect_start or si - bmark >= 4):
                can_inc = False
            if si  < total_sents - 1 and can_inc:
                if ch == cur.KEY_DOWN or ch == cur.KEY_RIGHT or nod_set:
                    si += 1
                    while (visible[si] == False or passable[si] == True) and si < total_sents -1:
                        si += 1
                    
                if ch != cur.KEY_DOWN: 
                    bmark = si
            else:
                cur.beep()
                show_info("Please use left or right arrow keys to go to the next sentnce.")
                if si > total_sents - 1:
                    si = total_sents - 1
        if ch == cur.KEY_UP or chr(ch) == '5':
            if si > 0: 
                si -= 1
                while visible[si] == False and si > 0:
                    si -= 1
            else:
                cur.beep()
                si = 0

        update_si = False
        if ch == ord('j'):
            if sc > 0:
                sc -= 1
                fc = art["sections"][sc]["frags_offset"]
                update_si = True
            else:
                cur.beep()
                sc = 0
        if ch == ord('k'):
            if sc < sects_num - 1:
                sc += 1
                fc = art["sections"][sc]["frags_offset"]
                update_si = True
            else:
                cur.beep()
                sc = sects_num -1
        if ch == ord(';'):
            if fc < total_frags - 1:
                fc += 1
                update_si = True
            else:
                cur.beep()
                fc = total_frags -1
        if ch == ord('l'):
            if fc > 0 :
                fc -= 1
                update_si = True
            else:
                cur.beep()
                fc = 0

        if ch == ord('.'):
            if start_row < cury:
                start_row += scroll
            else:
                cur.beep()

        if ch == ord(','):
            if start_row > 0:
                start_row -= scroll
            else:
                cur.beep()


        if ch == cur.KEY_PPAGE:
            si = max(si - 10, 0)
            bmark = si
        elif ch == cur.KEY_NPAGE:
            si = min(si + 10, total_sents -1)
            bmark = si
        elif ch == cur.KEY_HOME:
            si = 0
        elif ch == cur.KEY_END:
            si = total_sents -1 

        if update_si:
            fc = max(fc, 0)
            fc = min(fc, total_frags -1)
            si = frags_sents[fc][0]
            bmark = si
        c = 0 
        while c < sects_num  and si >= art["sections"][c]["sents_offset"]:
            c += 1
        sc = max(c - 1,0)
        f = 0
        while f < total_frags and si >= frags_sents[f][0]:
            f += 1
        fc = max(f - 1,0)

        art['sections'][sc]['fc'] = fc 
        if si < bmark:
            bmark = si
        if ch == ord('g'):
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
                        insert_article(tagged_articles, art)
                    else:
                        remove_article(tagged_articles, art)

                    save_obj(tagged_articles, "tagged_articles", "articles")
            text_win.clear()
            text_win.refresh(0,0, 2,0, rows -2, cols)
        if ch == ord('t'):
            choice = '' 
            while choice != 'q':
                choice, theme_menu,_ = show_menu(theme_menu, theme_options, title="theme")
            save_obj(theme_menu, conf["theme"], "theme")
            text_win.clear()
            text_win.refresh(0,0, 2,0, rows -2, cols)
        if ch == ord('q') or ch == 127: # before exiting artilce
            art["nods"] = nod
            art["times"] = rtime
            art["passable"] = passable
            art["visible"] = visible
            if nods_changed:
                insert_article(nod_articles, art)
                save_obj(nod_articles, "nod_articles", "articles")
            last_visited = load_obj("last_visited", "articles")
            insert_article(last_visited, art)
            save_obj(last_visited, "last_visited", "articles")
    return "" 

def refresh_menu(menu, menu_win, sel, options, shortkeys, subwins):
    global clG
    clear_screen(menu_win)
    row = 3 
    col = 5
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
       if k.startswith("sep"):
           if v:
               print_there(row, col,  str(v) + colon, menu_win, color)
       else:
           print_there(row, col, "{:<{}}".format(key, _m), menu_win, color, attr = cur.A_BOLD)
           if v != "button" and not k in subwins:
               print_there(row, gap, colon, menu_win, color, attr = cur.A_BOLD)

       if v != "button" and not k in subwins:
           if "color" in k:
               print_there(row, col + _m + 2, "{:^5}".format(str(v)), menu_win, color_map[k]) 
           elif not k.startswith("sep"):
               print_there(row, col + _m + 2, "{}".format(v), menu_win, TEXT_COLOR)

       row += 1
    for k, item in subwins.items():
       sub_menu_win = menu_win.subwin(item["h"],
                item["w"],
                item["y"],
                item["x"])
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
        win_info = cur.newwin(rows //2, cols//2, rows//4, cols//4) 
    win_info.bkgd(' ', cur.color_pair(color)) # | cur.A_REVERSE)
    win_info.erase()
    if len(msg) > cols - 15:
        msg = msg[:(cols - 16)] + "..."
    print_there(0,1," {} ".format(msg), win_info, color)
    win_info.clrtoeol()

def show_msg(msg, color=MSG_COLOR):
   show_info(msg + " press any key", color)
   std.getch()

def show_err(msg, color=ERR_COLOR, bottom = True):
    show_info(msg+ " press any key...", color, bottom)
    if not bottom:
        std.getch()

def load_preset(new_preset, options, folder=""):
    menu = load_obj(new_preset, folder)
    if menu == None and folder == "theme":
        dark ={'preset': 'dark',"sep1":"colors", 'text-color': '247', 'back-color': '234', 'item-color': '71', 'cur-item-color': '101', 'sel-item-color': '33', 'title-color': '28', "sep2":"reading mode","faint-color":'241' ,"highlight-color":'153', "inverse-highlight":"True", "bold-highlight":"True"}
        light = {'preset': 'light',"sep1":"colors", 'text-color': '233', 'back-color': '243', 'item-color': '18', 'cur-item-color': '235', 'sel-item-color': '111', 'title-color': '17', "sep2":"reading mode","faint-color":'241' ,"highlight-color":'119', "inverse-highlight":"True","bold-highlight":"True"}
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

def select_box(win, opts, ni):
    ch = 0
    win.border()
    while ch != 27 and ch != ord('q'):
        ni = max(ni, 0)
        ni = min(ni, len(opts)-1)
        clear_screen(win)
        show_submenu(win, opts, ni)
        ch = get_key(std)
        if ch == cur.KEY_RIGHT or ch == cur.KEY_LEFT:
           clear_screen(win)
           return ni
        if ch == cur.KEY_UP:
            ni -= 1
        elif ch == cur.KEY_DOWN:
            ni += 1
        else:
            cur.beep()
            show_info("Use right or left arrow keys to select the item!")

    clear_screen(win)
    return -1
    

def show_submenu(sub_menu_win, opts, si, is_color = False):
   win_rows, win_cols = sub_menu_win.getmaxyx()
   win_rows = min(win_rows-3, 10)
   start = si - win_rows // 2
   start = max(start, 0)
   if len(opts) > win_rows:
 	  start = min(start, len(opts)-win_rows)
   if start > 0:
 	  mprint("...", sub_menu_win, cW)
   for vi, v in enumerate(opts[start:start + win_rows]):
     if len(v) > win_cols:
         v = v[:win_cols - 5] + "..."
     if start + vi == si:
        sel_v = v
        if is_color:
            mprint("{:^8}".format(">" + str(v)), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
            mprint("{:<8}".format(str(v)),sub_menu_win, CUR_ITEM_COLOR)
     else:
        if is_color:
            mprint("{:^8}".format(v), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
            mprint("{:<8}".format(str(v)), sub_menu_win, ITEM_COLOR)
   if start + win_rows < len(opts):
 	  mprint("...", sub_menu_win, cW)
   sub_menu_win.refresh()

menu_win = None
common_subwin = None
def show_menu(menu, options, shortkeys={}, title = "", mi = 0, subwins={}, info = "h) help | q) quit"):
    global menu_win, common_subwin

    si = 0 #submenu index
    ch = 0 #user choice
    mode = 'm' # 'm' means we are in menu, 's' means we are in submenu

    rows, cols = std.getmaxyx()
    height = rows -1  
    width = cols 

    menu_win = cur.newwin(height, width, 0, 0)
    common_subwin = menu_win.subwin(5, width//2 + 5)

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
    while ch != ord('q'):
        sel,mi = get_sel(menu, mi)
        sub_menu_win = common_subwin
        key_set = False
        cmd = ""
        if not sel.startswith("sep"):
            clear_screen(sub_menu_win)
            if mode == 'm':
                refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
        if sel not in options and menu[sel] != "button" and not sel.startswith("sep"): 
             # menu[sel]=""
            cur_val = menu[sel]
            refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
            _m = max([len(x) for x in menu.keys()]) + 5  
            val, ch = minput(menu_win,row + mi, col, "{:<{}}".format(sel,_m) + ": ", default=menu[sel]) 
            if val != "<ESC>":
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
            sub_menu_win = menu_win.subwin(subwins[sel]["h"],
                subwins[sel]["w"],
                subwins[sel]["y"],
                subwins[sel]["x"])
        if mode == 's' and menu[sel] != "button":
            if sel in options:
              si = min(si, len(options[sel]) - 1)
              si = max(si, 0)
              show_submenu(sub_menu_win, options[sel], si, "color" in sel)

        if not sel.startswith('sep') and not key_set:
            ch = get_key(std)
            
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
        elif  ch == cur.KEY_ENTER or ch == 10 or ch == 13:
            is_button = menu[sel] == "button"
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
                if "preset" in menu and title == "theme":
                    reset_colors(menu)
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
            if menu[sel] != "button":
                old_val = menu[sel]
                if sel in options and menu[sel] in options[sel]:
                    si = options[sel].index(menu[sel]) 
                mode = 's'
                st = ""
        elif ch == cur.KEY_LEFT or ch == 27:
            if old_val != "":
                menu[sel] = old_val
                refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
                if "color" in sel:
                    reset_colors(menu)
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
                new_item = options[sel][0] if len(options[sel]) > 0 else "None"
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
            refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
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
        elif ch != ord('q') and chr(ch) in shortkeys:
            mi = list(menu.keys()).index(shortkeys[chr(ch)])
            sel,mi = get_sel(menu, mi)
            refresh_menu(menu, menu_win, sel, options, shortkeys, subwins)
            if menu[sel] == "button":
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

def main(stdscr):
    global template_menu, template_options, theme_options, theme_menu, std, conf, query, filters

    std = stdscr
    # mouse = cur.mousemask(cur.ALL_MOUSE_EVENTS)
    cur.start_color()
    # cur.curs_set(0) 
    # std.keypad(1)
    cur.use_default_colors()

    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    menu =  None # load_obj("main_menu", "")
    isFirst = False
    if menu is None:
        isFirst = True
        menu = {"website articles":"button", "webpage":"button", "search articles":"button", "settings":"button","tagged articles":"button", "nods":"button", "text files":"button","sep3":"","recent articles":""}
    options = {
            "saved articles":["None"],
            "recent articles":["None"],
            }



    last_visited = load_obj("last_visited", "articles")
    if last_visited is None:
        last_visited = []
    recent_arts = []
    for art in last_visited[:10]:
        recent_arts.append(art["title"][:60]+ "...")
    subwins = {"recent articles":{"x":7,"y":12,"h":8,"w":68}}
    options["recent articles"] =recent_arts 

    data_dir = user_data_dir(appname, appauthor) + "/articles"

    saved_articles =  [Path(f).stem for f in Path(data_dir).glob('*') if f.is_file()]
    if not saved_articles:
        options["saved articles"] =["None"] 
    else:
        options["saved articles"] = saved_articles

    if isFirst:
        for opt in menu:
           if opt in options:
               menu[opt] = options[opt][0] if options[opt] else ""

    conf = load_obj("conf", "")
    if conf is None:
        conf = {"theme":"default", "template":"txt"}

    colors = [str(y) for y in range(-1, cur.COLORS)]
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
    clear_screen(std)
    ch = 'a'
    shortkeys = {"r":"recent articles","g":"tagged articles", "p":"webpage", "s":"search articles","w":"website articles", "o":"saved articles", 't':"text files"}
    mi = 0
    while ch != 'q':
        info = "h) help         q) quit"
        show_info(info)
        ch, menu, mi = show_menu(menu, options, shortkeys = shortkeys, mi = mi, subwins = subwins)
        save_obj(menu, "main_menu", "")
        if ch == "search articles":
            search()
        elif ch == "webpage":
            # webpage()
            list_tags()
        elif ch == 'g' or ch == "tegged articles":
            list_tags()
        if ch == 'h' or ch == "help":
            show_info(('\n'
                       'Press the key associated to each item, for example presss s to search articles'
                       ' Arrow keys)   next, previous item\n'
                       ' PageUp/Down)  First/Last item\n'
                       ' d)            delete an item from list  \n'
                       '\n\n Press any key to close ...'),
                       bottom=False)
            win_info.getch()
        elif ch == 'text files':
            text_files =  [Path(f).name for f in Path(".").glob('*.txt') if f.is_file()]
            articles = []
            for text in text_files:
                with open(text, "r") as f:
                    data = f.read()
                title, i = get_title(data, text)
                if i > 0:
                    data = data[i:]
                art = {"id":text, "pdfUrl":text, "title":title, "sections":get_sects(data)}
                articles.append(art)
            ret = list_articles(articles, text)
        elif ch == 'w' or ch == "website articles":
             website()
        elif ch == "nods":
             list_nods()
        elif ch == "r" or ch == "recent articles":
             si = options["recent articles"].index(menu["recent articles"]) 
             show_article(last_visited[si])
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

def list_nods():
    clear_screen(std)
    subwins = {
            "nods":{"x":7,"y":5,"h":15,"w":68},
            }
    choice = ''
    opts, art_list = refresh_nods()
    mi = 0
    while choice != 'q':
        nods = ""
        menu = {"nods":""} 
        choice, menu,mi = show_menu(menu, opts,
                shortkeys={"n":"nods"},
                subwins=subwins, mi=mi, title="nods")
        if choice == "nods":
            sel_nod = menu["nods"][:-5]
            sel_nod = sel_nod.strip()
            articles = art_list[sel_nod]
            if len(articles) > 0:
                ret = list_articles(articles, sel_nod, True)
            opts, art_list = refresh_nods()

def refresh_nods():
    nod_articles = load_obj("nod_articles","articles", [])
    N = len(nod_articles)
    art_num = {}
    art_list = {}
    nod_list = []
    for art in nod_articles:
        if not "nods" in art:
            continue
        art_nods = art["nods"]
        for nod in art_nods:
            nod = nod.strip()
            if nod == "OK" or nod == "":
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
    opts = {"nods":[]}
    for nod in nod_list:
        opts["nods"].append(nod.ljust(40) + str(art_num[nod]))
    return opts, art_list

def refresh_tags():
    tagged_articles = load_obj("tagged_articles","articles")
    N = len(tagged_articles)
    art_num = {}
    art_list = {}
    tag_list = []
    for art in tagged_articles:
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
    clear_screen(std)
    subwins = {
            "tags":{"x":7,"y":5,"h":15,"w":68},
            }
    choice = ''
    opts, art_list = refresh_tags()
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
    ch = 'a'
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
                 config.fetch_images = False
                 #config.follow_meta_refresh = True
                 try:
                     site = newspaper.build(site_addr, memoize_articles = False) # config)
                     # logging.info(site.article_urls())
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

                     #a.nlp()
                     art = {"id":a.title,"pdfUrl":a.url, "title":a.title, "sections":get_sects(a.text)}
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
    ch = 'a'
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
    menu = None # load_obj("query_menu", "")
    isFirst = False
    if menu is None:
        isFirst = True 
        menu = {"last results":"button", "keywords":"reading comprehension", "year":"","task":"", "conference":"", "dataset":"","sep1":"", "search":"button", }
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
    ch = 'a'
    last_query = menu["keywords"]
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
                    articles,ret = request(0)
                    fid = menu["keywords"] + '_' + menu["year"] + '_1_' + menu["conference"] + '_' + menu["task"] + '_' + menu["dataset"]
                    fid = fid.replace(' ','_')
                    fid = fid.replace('__','_')
                    fid = fid.replace('__','_')
                    if len(articles) > 0 and ret == "":
                        if isinstance(articles, tuple):
                            articles = articles[0]
                        save_obj(articles, "last_results", "")
                        ret = list_articles(articles, fid)
                    if ret:
                        show_err(ret[:200]+ "...", bottom = False)

                elif ch == 'l' or ch == "last results":
                     query = last_query
                     last_results_file = user_data_dir(appname, appauthor) + "/last_results.pkl"
                     obj_file = Path(last_results_file) 
                     if  obj_file.is_file():
                        cr_time = time.ctime(os.path.getmtime(last_results_file))
                        cr_date = datetime.datetime.strptime(str(cr_time), "%a %b %d %H:%M:%S %Y")
                     articles = load_obj("last_results", "")
                     if articles != None:
                         ret = list_articles(articles, "results at " + str(cr_date))
                     else:
                         show_err("Last results is missing....")

            except KeyboardInterrupt:
                choice = ord('q')
                show_cursor()
    save_obj(menu, "query_menu", "")

if __name__ == "__main__":
    wrapper(main)
