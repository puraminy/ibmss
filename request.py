import requests
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
import curses as cur
from curses import wrapper
from pathlib import Path
from urllib.parse import urlparse
from appdirs import *
import logging, sys
logging.basicConfig(filename='nodreader.log', level=logging.DEBUG)

appname = "NodReader"
appauthor = "App"

std = None
theme_opts = {}
theme_ranges = {}
conf = {}
nods = {}
times = {}
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
        "okay?":242,
        "yes":148,
        "okay":178,
        "didn't get":218,
        "interesting!":248,
        "so?":118,
        "got it!":98,
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


def reset_colors(theme, bg = None):
    if bg is None:
        bg = int(theme["back-color"])
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

def save_obj(obj, name, directory):
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

def del_obj(name, directory):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    fname = folder + '/' + name + '.pkl'
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return None 
    else:
        obj_file.unlink()

# Add or remove an item from the list of selected sections of articles
def add_remove_sels(d, art, ch):
    key = art["id"] # article id
    sects = 'abstract introduction conclusion'
    if not key in d:
        if ch == ord('s'):
           d[key] = sects.split(' ')
        else:
           d[key] = [s["title"].lower() for s in art["sections"]]
    else: 
        del d[key]
    save_obj(d, "sels", "")

def get_frags(text):
    logging.info(text)
    parts = text.split("\n")
    parts = list(filter(None, parts)) 
    frags = []
    for t in parts:
        frag = {"text":t}
        frags.append(frag)
    return frags

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

    # print(data)
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

def list_articles(articles, fid):
    N = len(articles)
    if N == 0:
        return "No result fond!"
    rows, cols = std.getmaxyx()
    main_win = cur.newwin(rows-2, cols-5, 3, 5)
    width = cols - 10
    main_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    sels = load_obj("sels","")
    if sels is None:
        sels = {}
    ch = 0
    start = 0
    k = 0
    while ch != ord('q'):
        clear_screen(std)
        main_win.clear()
        print_there(2, 5, fid, std)
        for j,a in enumerate(articles[start:start + 15]): 
            i = start + j
            paper_title =  a['title']
            dots = ""
            if len(paper_title) > width - 10:
               dots = "..."
            item = "{}{} {}".format(i, ":", paper_title[:width - 10] + dots)               
            color = ITEM_COLOR
            if a["id"] in sels:
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
            show_article(articles[k])
        if ch == cur.KEY_UP:
            k -= 1
        if ch == cur.KEY_DOWN:
            k +=1

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
                show_info("Getting articles...")
                new_articles, ret = request(page + 1)
                # with open("tt.txt", "w") as f:
                #    print(str(new_articles), file =f)
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
                       ' s)          select an article\n'
                       ' w)          save all or selected items\n'
                       ' e)          export all or selected items\n'
                       ' t)          change color theme\n'
                       ' HOME)       go to the first item\n'
                       ' END)        go to the last item\n'
                       ' PageUp)     previous page\n'
                       ' Arrow keys) next, previous article\n'
                       ' q)          return back to the search menu\n'
                       '\n\n Press any key to close ...'),
                       bottom=False)
            win_info.getch()
        if ch == ord('w'):
            if not sels:
                show_err("No article was selected")
            else:
                sel_arts = []
                count = 0
                for a in articles:
                    count += 1
                    if a["id"] in sels:
                        fid += str(count)
                        sel_arts.append(a)
                fname = minput(win_info, 0, 1, "Save articles as:", default = fid) 
                if fname != "<ESC>":
                    save_obj(sel_arts, fname, "articles")
                    show_info("Selected articles were saved as " + fname)
        if ch == ord('x') or ch == ord('m'):
            merge = ch == 'm'
            if not sels:
                show_err("No article was selected!! Select an article using s")
            else:
                if merge:
                    f = open(fid + '.html', "w")
                    print("<!DOCTYPE html>\n<html>\n<body>", file=f)
                elif not os.path.exists(fid):
                    os.makedirs(fid)
                num = 0
                for j,a in enumerate(articles): 
                    i = start + j
                    _id = a["id"]
                    if  _id not in sels:
                        continue
                    num += 1
                    paper_title = a['title']
                    show_info(paper_title + '...')
                    file_name = paper_title.replace(' ','_').lower()
                    if not merge:
                       f = open(fid + '/' + file_name + '.html', "w")
                       print("<!DOCTYPE html>\n<html>\n<body>", file=f)
                    print("<h1>" +  "New Paper" + "</h1>", file=f)
                    print("<h1>" +  paper_title + "</h1>", file=f)
                    for b in a['sections']:
                        title =  b['title']
                        _sects = sels[_id]
                        if not title.lower() in _sects:
                            continue
                        print("<h2>", file=f)
                        print(title, file=f)
                        print("</h2>", file=f)
                        for c in b['fragments']:
                                text= c['text']
                                f.write("<p>" + text + "</p>")

                        print("<p> Paper was:" +  paper_title + "</p>", file=f)
                    print("</body>\n</html>", file=f)
                    if not merge:
                      f.close()
                #for
                if merge:
                    f.close()
                show_msg(str(num)+ " articles were downloaded and saved into:" + fid)
            ch = get_key(std)

def show_article(art):

    global theme_opts, theme_ranges

    rows, cols = std.getmaxyx()
    sects_num = 0
    sels = load_obj("sels","")
    if sels is None:
        sels = {}
    k,sc  = 0,0
    fast_read = False
    show_prev = False
    break_to_sent = False 
    start_row = 0
    text_win = cur.newpad(rows*50, cols - 10)
    main_win = cur.newwin(rows, cols, 0, 0)
    text_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    main_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    width = cols - 10 

    # text_win = std
    bg = ""
    last_visited = load_obj("last_visited", "articles")
    if last_visited is None:
        last_visited = []
    if not art in last_visited:
        last_visited.insert(0, art)
    else:
        last_visited.remove(art)
        last_visited.insert(0, art)

    save_obj(last_visited, "last_visited", "articles")
    expand = 3
    frags_text = ""
    art_id = -1
    si = 0
    bmark = 0
    fc = 1
    cury = 0
    nod = {}
    rtime = {}
    page_height = rows - 4
    scroll = 1
    show_reading_time = False
    start_reading = True
    pos = {} 
    cur_sent = "1"
    is_section = False
    art_id = art['id']
    if art_id != 0 and nod:
       nods[art_id] = nod
       save_obj(nods, "nods", "")
    if art_id != 0 and rtime:
       times[art_id] = rtime
       save_obj(times, "times", "")
       # with open(art_id + ".txt", "w") as ff:
       #    print(art, file = ff)
    if art_id in nods:
       nod = nods[art_id]
    else:
       nod = {}
    if art_id in times:
       rtime = times[art_id]
    else:
       rtime = {}
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
    while ch != ord('q') and ch != 127:
        # clear_screen(text_win)
        start_row = max(0, start_row)
        start_row = min(cury - 1, start_row)
        if bg != theme_opts["back-color"]:
            clear_screen(main_win)
            bg = theme_opts["back-color"]
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
                    if art_id in sels and b["title"].lower() in sels[art_id]:
                        _color = SEL_ITEM_COLOR
                    else:
                        _color = CUR_ITEM_COLOR
            else:
                sect_title = b["title"]
 
            if sect_title != "all":
                mprint(sect_title, text_win, _color, attr = cur.A_BOLD)
            pos[fsn],_ = text_win.getyx()
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
                       if True:
                           for sent in frag_sents:
                               feedback = nod[fsn] if fsn in nod else "okay?"
                               reading_time = rtime[fsn][1] if fsn in rtime else 0 
                               f_color = SEL_ITEM_COLOR
                               # f_color = nod_color[feedback]
                               if start_reading and feedback != "okay?":
                                   color = FAINT_COLOR
                               else:
                                   color = TEXT_COLOR
                               if show_reading_time:
                                   f_color = scale_color(reading_time)
                                   mprint(str(reading_time), text_win, f_color)
                               sent = "\n".join(textwrap.wrap(sent, width -5))
                               if fsn >= bmark and fsn <= si:
                                   cur_sent = sent
                                   mprint(sent, text_win, hlcolor, end= " ")
                               else:
                                   mprint(sent, text_win, color, end=" ")
                               if feedback != 'okay?':
                                   fline = "-"*20
                                   if feedback == 'yes':
                                       feedback = u'\u2713'
                                   #mprint("\n" + fline, text_win, FAINT_COLOR)
                                   mprint(feedback, text_win, f_color, end=" ")
                                   #mprint(fline, text_win, FAINT_COLOR)
                               mprint("", text_win, f_color)
                               pos[fsn],_ = text_win.getyx()
                               fsn += 1
                       
                       mprint("\n", text_win, color)
                       ffn += 1
                     # end for fragments
            sn += 1
         # end for sections
 
        #print(":", end="", flush=True)
        cury, curx = text_win.getyx()
        sc = min(sc, sects_num)
        f_offset = art['sections'][sc]['frags_offset'] 
        offset = art["sections"][sc]["sents_offset"] 
        show_info("frags:"+ str(total_frags) + " start row:" + str(start_row) + " frag offset:"+ str(f_offset)  + " fc:" + str(fc) + " si:" + str(si) + " sent offset:" + str(offset))
        if si in pos and not ch == ord('.') and not ch == ord(','):
            if pos[si] > 10:    
                start_row = pos[si] - 10 
            else:
                start_row = 0

        text_win.refresh(start_row,0, 2,5, rows -2, cols- 5)
        if is_section and cur_sent.lower() in ['all', 'summary', 'abstract', 'introduction','conclusion', 'related works']:
            pass
        else:
            ch = get_key(std)
        if ch == ord('u'):
            with open(art["title"]  + ".txt","w") as f:
                print(art, file = f)
        if ch == ord('l'):
           if nod:
               si = 0
               while si in nod and nod[si] != "okay?":
                   si += 1
               si = min(si, total_sents - 1)

        if ch == ord('r'):
            start_reading = not start_reading
        if ch == ord('z'):
            show_reading_time = not show_reading_time

        if ch == ord('q') or ch == 127:
            start_row = 0
            if art_id != 0 and nod:
               nods[art_id] = nod
               save_obj(nods, "nods", "")
            if art_id != 0 and rtime:
               times[art_id] = rtime
               save_obj(times, "times", "")
        if ch == ord('x'):
            fast_read = not fast_read
        if ch == ord('f') or ch == ord('s'):
            add_remove_sels(sels, art, ch)
        if ch == ord('e'):
            if expand < 3:
                expand += 1
        if ch == ord('c'):
            if expand > 0:
                expand -= 1
        if ch == ord('a'):
            for ss in range(start,start+15):
                  rr = articles[ss]
                  add_remove_sels(sels, rr, 's')

        if ch == ord('s'):
            cur_sect = art["sections"][sc]["title"].lower()
            if art_id in sels:
                if cur_sect in sels[art_id]:
                    sels[art_id].remove(cur_sect)
                else:
                    sels[art_id].append(cur_sect)
            else:
                sels[art_id] = [cur_sect]

        if (ch == cur.KEY_LEFT or ch == cur.KEY_RIGHT or ch == cur.KEY_DOWN or chr(ch).isdigit()):
            _nod = nod[si] if si in nod else "okay?"
            if chr(ch) == '1' or ch == cur.KEY_LEFT:
                _nod = "so?"
            elif chr(ch) == 'o':
                _nod = "okay"
            elif ch == cur.KEY_RIGHT or chr(ch) == "3":
                _nod = "yes"
            elif chr(ch) == "6":
                _nod = "interesting!"
            elif chr(ch) == "4" or chr(ch) == "-":
                _nod = "didn't get"
            elif chr(ch) == "+":
                _nod = "got it!"
#            
            for ii in range(bmark, si +1):
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
            if si  < total_sents - 1:
                si += 1
                if si in nod and nod[si] != "okay?":
                    bmark = si 
                elif (ch != cur.KEY_DOWN and ch != '2'):
                    bmark = si
                elif (si -1) in nod and nod[si -1] != "okay?":
                    bmark = si    
            else:
                cur.beep()
                si = total_sents - 1
        if ch == cur.KEY_UP or ch == ord('5'):
            if si > 0: 
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
        elif ch == cur.KEY_NPAGE:
            si = min(si + 10, total_sents -1)
        elif ch == cur.KEY_HOME:
            si = 0
        elif ch == cur.KEY_END:
            si = total_sents -1 

        if update_si:
            fc = max(fc, 0)
            fc = min(fc, total_frags -1)
            si = frags_sents[fc][0]
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
        if ch == ord('t'):
            _, theme_opts,_ = show_menu(theme_opts, theme_ranges, title="theme")
            save_obj(theme_opts, conf["theme"], "theme")
    return "" 

def refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins):
    global clG
    clear_screen(menu_win)
    row = 3 
    col = 5
    _m = max([len(x) for x in opts.keys()]) + 5  
    gap = col + _m
    for k, v in opts.items():
       colon = ":" # if not k in ranges else ">"
       key = k
       if k in shortkeys.values():
           sk = list(shortkeys.keys())[list(shortkeys.values()).index(k)]
           key = sk + ") " + k
       if k == sel:
           if k.startswith("sep"):
               print_there(row, col,  str(v) + colon,  menu_win, CUR_ITEM_COLOR)
           else:
               print_there(row, col, "{:<{}}".format(key, _m), menu_win, CUR_ITEM_COLOR, attr = cur.A_BOLD)
               if v != "button":
                   print_there(row, gap, colon, menu_win, CUR_ITEM_COLOR, attr = cur.A_BOLD)
       else:
           if k.startswith("sep"):
               print_there(row, col,  str(v) + colon, menu_win, TITLE_COLOR)
           else:
               print_there(row, col, "{:<{}}".format(key, _m), menu_win, ITEM_COLOR, attr = cur.A_BOLD)
               if v != "button":
                   print_there(row, gap, colon, menu_win, ITEM_COLOR, attr = cur.A_BOLD)

       if v != "button" and not k in subwins:
           if "color" in k:
               print_there(row, col + _m + 2, "{:^5}".format(str(v)), menu_win, color_map[k]) 
           elif not k.startswith("sep"):
               print_there(row, col + _m + 2, "{}".format(v), menu_win, TEXT_COLOR)

       row += 1
    for k, item in subwins.items():
       sub_menu_win = menu_win.subwin(item["h"], item["w"], item["y"], item["x"])
       sub_menu(sub_menu_win, opts, ranges, k, -1)

def get_sel(opts, mi):
    mi = max(mi, 0)
    mi = min(mi, len(opts)-1)
    return list(opts)[mi], mi

win_info = None
def show_info(msg, color=INFO_COLOR, bottom = True):
    global win_info
    rows, cols = std.getmaxyx()
    if bottom:
        win_info = cur.newwin(1, cols, rows-1,0) 
    else:
        win_info = cur.newwin(rows //2, cols//2, rows//4,cols//4) 
    win_info.bkgd(' ', cur.color_pair(color)) # | cur.A_REVERSE)
    win_info.erase()
    if len(msg) > cols - 2:

        msg = msg[:(cols - 5)] + "..."
    print_there(0,1," {} ".format(msg), win_info, color)
    win_info.clrtoeol()

def show_msg(msg, color=INFO_COLOR):
   show_info(msg, color)

def show_err(msg, color=ERR_COLOR, bottom = True):
    show_info(msg, color, bottom)
    win_info.getch()

def load_preset(new_preset, folder=""):
    opts = load_obj(new_preset, folder)
    if opts == None and folder == "theme":
        dark ={'preset': 'dark',"sep1":"colors", 'text-color': '247', 'back-color': '234', 'item-color': '71', 'cur-item-color': '101', 'sel-item-color': '148', 'title-color': '28', "sep2":"reading mode","faint-color":'241' ,"highlight-color":'153', "inverse-highlight":"True"}
        light = {'preset': 'light',"sep1":"colors", 'text-color': '142', 'back-color': '253', 'item-color': '12', 'cur-item-color': '35', 'sel-item-color': '39', 'title-color': '28', "sep2":"reading mode","faint-color":'251' ,"highlight-color":'119', "inverse-highlight":"True"}
        save_obj(dark, "dark", "theme")
        save_obj(light, "light", "theme")
        theme_ranges["preset"] = ["dark", "light"]
        new_preset = "dark"
        opts = dark

    opts["preset"] = new_preset
    if folder == "theme":
        reset_colors(opts)
    conf[folder] = new_preset
    save_obj(conf, "conf", "")
    return opts

def sub_menu(sub_menu_win, opts, ranges, sel, si):
   start = si - 5
   start = max(start, 0)
   if len(ranges[sel]) > 10:
 	  start = min(start, len(ranges[sel])-10)
   if start > 0:
 	  mprint("...", sub_menu_win, cW)
   for vi, v in enumerate(ranges[sel][start:start+10]):
     if start + vi == si:
        sel_v = v
        if "color" in sel:
            mprint("{:^8}".format(">" + str(v)), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
            mprint("{:<8}".format(str(v)),sub_menu_win, CUR_ITEM_COLOR)
     else:
        if "color" in sel:
            mprint("{:^8}".format(v), sub_menu_win, int(v), attr = cur.A_REVERSE) 
        else:
            mprint("{:<8}".format(str(v)), sub_menu_win, ITEM_COLOR)
   if "color" in sel:
 	  opts[sel] = sel_v
 	  reset_colors(opts)
   if start + 10 < len(ranges[sel]):
 	  mprint("...", sub_menu_win, cW)
   sub_menu_win.refresh()

def show_menu(opts, ranges, shortkeys={}, title = "", mi = 0, subwins={}):
    si = 0
    ch = 'a'
    mode = 'm'

    rows, cols = std.getmaxyx()
    height = rows -1  
    width = cols 

    menu_win = cur.newwin(height, width, 0, 0)
    common_subwin = menu_win.subwin(5, width//2 + 5)

    menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    common_subwin.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)

    mprint(title.center(rows), menu_win)
    hide_cursor()
    _help = False
    last_preset = conf["theme"]
    
    row = 3 
    col = 5
    mt, st = "", ""
    old_val = ""
    while ch != ord('q'):
        sel,mi = get_sel(opts, mi)
        sub_menu_win = common_subwin
        if sel in subwins:
            sub_menu_win = menu_win.subwin(subwins[sel]["h"],
                    subwins[sel]["w"],
                    subwins[sel]["y"],
                    subwins[sel]["x"])

        if not sel.startswith("sep"):
            clear_screen(sub_menu_win)
            if mode == 'm':
                refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
        if sel not in ranges and opts[sel] != "button" and not sel.startswith("sep"): 
             # opts[sel]=""
            cur_val = opts[sel]
            refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
            _m = max([len(x) for x in opts.keys()]) + 5  
            val = minput(menu_win,row + mi, col, "{:<{}}".format(sel,_m) + ": ", default=opts[sel]) 
            if val != "<ESC>":
                 opts[sel] = val
            else:
                 opts[sel] = cur_val
            mi += 1
            sel,mi = get_sel(opts, mi)
            refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
            mode = 'm'
            mt = ""
        if (mode == 's') and opts[sel] != "button":
            if sel in ranges:
              si = min(si, len(ranges[sel]) - 1)
              si = max(si, 0)
              sub_menu(sub_menu_win, opts, ranges, sel, si)

        if not sel.startswith('sep'):
            ch = get_key(std)
            
        if ch == cur.KEY_DOWN:
            if mode == "m":
                mi += 1
            elif sel in ranges:
                si += 1
        elif ch == cur.KEY_UP:
            if mode == "m":
                mi -= 1
            elif sel in ranges:
                si -= 1
        elif ch == cur.KEY_NPAGE:
            if mode == "m":
                mi += 10
            elif sel in ranges:
                si += 10
        elif ch == cur.KEY_PPAGE:
            if mode == "m":
                mi -= 10
            elif sel in ranges:
                si -= 10
        elif  ch == cur.KEY_ENTER or ch == 10 or ch == 13:
            if opts[sel] == "button":
              return sel, opts, mi 
            if sel in ranges:
                si = min(si, len(ranges[sel]) - 1)
                si = max(si, 0)
            if sel.startswith("sep"):
                mi += 1
            if mode == 'm':
                old_val = opts[sel]
                mode = 's'
                st = ""
                if sel in ranges:
                    si = ranges[sel].index(opts[sel])
            elif mode == 's':
                opts[sel] = ranges[sel][si]
                if "preset" in opts:
                    reset_colors(opts)
                if sel == "preset":
                    save_obj(opts, last_preset, title)
                    new_preset = opts[sel]
                    opts = load_preset(new_preset, title)
                    last_preset = new_preset
                    refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
                    show_info(new_preset +  " was loaded")
                if sel in shortkeys.values():
                    return sel, opts, mi
                mode = 'm'    
                mt = ""
                si = 0
                old_val = ""
        elif ch == cur.KEY_RIGHT:
            if opts[sel] != "button":
                old_val = opts[sel]
                if sel in ranges and opts[sel] in ranges[sel]:
                    si = ranges[sel].index(opts[sel]) 
                    mode = 's'
                    st = ""
        elif ch == cur.KEY_LEFT or ch == 27:
            if old_val != "":
                opts[sel] = old_val
                refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
                if "color" in sel:
                    reset_colors(opts)
            old_val = ""
            mode = 'm'
            mt = ""
        elif ch == ord('d'):
            if mode == 'm':
                item = opts[sel]
            else:
                item = ranges[sel][si]
            confirm = minput(win_info, 0, 1, 
                    "Are you sure you want to delete " + item + "? (y/n)",
                    accept_on = ['y','Y','n','N'])

            if confirm == "y" or confirm == "Y":
                del_obj(item, title)
                ranges[sel].remove(item)
                save_obj(ranges[sel],sel,title)
                new_item = ranges[sel][0] if len(ranges[sel]) > 0 else "None"
                opts[sel] = new_item
                if sel == "preset":
                    opts = load_preset(new_item, title)
                    last_preset = new_item
                    refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
                    show_info(new_item +  " was loaded")
                else:
                    show_info(item +  " was deleted")
                si = 0

        elif ch == ord('s') and "preset" in opts:
            fname = minput(win_info, 0, 1, "Save as:") 
            if fname != "<ESC>":
                save_obj(opts, fname, title)
                reset_colors(opts)
                show_info(opts["preset"] +  " was saved as " + fname)
                opts["preset"] = fname
                ranges["preset"].append(fname)
                last_preset = fname
                refresh_menu(opts, menu_win, sel, ranges, shortkeys)
        elif chr(ch) in shortkeys:
            mi = list(opts.keys()).index(shortkeys[chr(ch)])
            sel,mi = get_sel(opts, mi)
            refresh_menu(opts, menu_win, sel, ranges, shortkeys, subwins)
            if opts[sel] == "button":
                return sel, opts, mi
            old_val = opts[sel]
            mode = 's'
            st = ""
        else:
            if mode == 's' and chr(ch).isdigit() and sel in ranges:
                si,st = find(ranges[sel], st, chr(ch), si)
            else:
                cur.beep()
    return ch, opts, mi

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
    global theme_ranges, theme_opts, std, conf, times, nods, query, filters


    std = stdscr
    cur.start_color()
    cur.use_default_colors()

    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    opts =  None # load_obj("main_opts", "")
    isFirst = False
    if opts is None:
        isFirst = True
        opts = {"website articles":"button", "webpage":"button", "search articles":"button", "settings":"button","saved articles":"", "text files":"button","sep3":"","recent articles":""}
    ranges = {
            "saved articles":["None"],
            "recent articles":["None"],
            }



    last_visited = load_obj("last_visited", "articles")
    if last_visited is None:
        last_visited = []
    recent_arts = []
    for art in last_visited[:10]:
        recent_arts.append(art["title"][:60]+ "...")
    subwins = {"recent articles":{"x":7,"y":12,"h":7,"w":68}}
    ranges["recent articles"] =recent_arts 

    data_dir = user_data_dir(appname, appauthor) + "/articles"

    saved_articles =  [Path(f).stem for f in Path(data_dir).glob('*') if f.is_file()]
    if not saved_articles:
        ranges["saved articles"] =["None"] 
    else:
        ranges["saved articles"] = saved_articles

    if isFirst:
        for opt in opts:
           if opt in ranges:
               opts[opt] = ranges[opt][0] if ranges[opt] else ""

    conf = load_obj("conf", "")
    if conf is None:
        conf = {"theme":"default"}
    nods = load_obj("nods", "")
    times = None # load_obj("times", "")
    if nods is None:
        nods = {}
    if times is None:
        times = {}

    colors = [str(y) for y in range(-1, cur.COLORS)]
    theme_ranges = {
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
            }

    theme_opts = load_preset(conf["theme"], "theme") 
    # mprint(str(theme_opts),std)
    # std.getch()

    themes_dir = user_data_dir(appname, appauthor) + "/theme"
    saved_themes =  [Path(f).stem for f in Path(themes_dir).glob('*') if f.is_file()]
    if not saved_themes:
        theme_ranges["preset"] =["default"] 
    else:
        theme_ranges["preset"] = saved_themes

    reset_colors(theme_opts)
    #os.environ.setdefault('ESCDELAY', '25')
    #ESCDELAY = 25
    clear_screen(std)
    ch = 'a'
    shortkeys = {"q":"quit","r":"recent articles", "p":"webpage", "s":"search articles","w":"website articles", "o":"saved articles", 't':"text files"}
    mi = 0
    while ch != 'q':
        info = "h) help         q) quit"
        show_info(info)
        ch, opts, mi = show_menu(opts, ranges, shortkeys = shortkeys, mi = mi, subwins = subwins)
        if type(ch) is int:
            ch = chr(ch)
        save_obj(opts, "main_opts", "")
        if ch == "search articles":
            search()
        elif ch == "webpage":
            webpage()
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
                art = {"id":text, "pdfUrl":text, "title":text, "sections":[{"title":"all", "fragments":[{"text":data}]}]}
                articles.append(art)
            ret = list_articles(articles, text)
        elif ch == 'w' or ch == "website articles":
             website()
        elif ch == 'o' or ch == "saved articles" or ch=="recent articles":
             selected = "last_visited" if ch=="recent articles" else opts["saved articles"]
             if selected == None:
                 show_err("Please select articles to load")
             else:
                 articles = load_obj(selected, "articles")
                 if articles != None:
                     ret = list_articles(articles, "sel articles")
                 else:
                     show_err("Unable to load the file....")

def website():

    opts =  load_obj("web_opts", "")
    isFirst = False
    if opts is None:
        opts = {"address":"", "load":"button", "popular websites":"", "saved websites":""}
        isFirst = True

    shortkeys = {"l":"load", "p":"popular websites", 's':"saved websites"}
    ws_dir = user_data_dir(appname, appauthor) + "/websites"
    saved_websites =  [Path(f).stem for f in Path(ws_dir).glob('*') if f.is_file()]
#    if saved_websites:
#        opts["sep1"] = "saved websites"
#    c = 1 
#    for ws in reversed(saved_websites):
#        opts[ws] = "button"
#        shortkeys[str(c)] = ws
#        c += 1
    ranges = {"history":["None"], "bookmarks":["None"]}
    ranges["popular websites"] = newspaper.popular_urls()
    ranges["saved websites"] = saved_websites
    history = load_obj("history", "")
    if history is None:
        history = ["None"]
    elif "None" in history:
        history.remove("None")
    ranges["history"] = history
    if isFirst:
        for opt in opts:
           if opt in ranges:
               opts[opt] = ranges[opt][0] if ranges[opt] else ""
    clear_screen(std)
    ch = 'a'
    mi = 0
    subwins = {"saved websites":{"x":28,"y":7,"h":10,"w":38}}
    while ch != 'q':
        info = "s) search l) open last results  h) other shortkeys         q) quit"
        show_info(info)
        ch, opts, mi = show_menu(opts, ranges, shortkeys = shortkeys, mi = mi, subwins= subwins)

        if type(ch) is int: 
            ch = chr(ch)
        site_addr = ""
        if ch == 'l' or ch == "load":
            site_addr = opts["address"]
        if ch == "popular websites":
            site_addr = opts["popular websites"]
        if site_addr != "":
             show_info("Gettign articles from " + site_addr)
             config = newspaper.Config()
             config.memoize_articles = False
             config.fetch_images = False
             config.follow_meta_refresh = True
             try:
                 site  = newspaper.build(site_addr, memoize_articles = False) #, config)
                 # site.download()
                 # site.generate_articles()
             except Exception as e:
                 show_err("error: " + str(e))
                 if ch == 'l' or ch == "load":
                     mi = 0
                 continue
             if not site_addr in history:
                 history.append(site_addr)
                 save_obj(history, "history", "")
             articles = []
             for a in site.articles:
                 try:
                     a.download()
                     a.parse()
                 except:
                     continue
                 #a.nlp()
                 art = {"id":a.title,"pdfUrl":a.url, "title":a.title, "sections":[{"title":"all", "fragments":get_frags(a.text)},{"title":"summary", "fragments":[{"text":a.summary}]}]}
                 articles.append(art)
             if articles != []:
                 uri = urlparse(site_addr)
                 save_obj(articles, uri.netloc, "websites")
                 ret = list_articles(articles, site_addr)
             else:
                 show_err("No article was found...")
             
        elif ch == "saved websites":
             selected = opts["saved websites"]
             if selected == "":
                 show_err("Please select articles to load")
             else:
                 articles = load_obj(selected, "websites")
                 if articles != None:
                     ret = list_articles(articles, "sel articles")
                 else:
                     show_err("Unable to load the file....")
    save_obj(opts, "web_opts", "")

def webpage():

    opts =  load_obj("webpage_opts", "")
    isFirst = False
    if opts is None:
        opts = {"address":"", "load":"button", "recent pages":""}
        isFirst = True

    shortkeys = {"l":"load", "r":"recent pages"}
    ranges = {}

    recent_pages = load_obj("recent_pages", "articles")
    if recent_pages is None:
        recent_pages = []
    arts = []
    for art in recent_pages[:10]:
        arts.append(art["title"][:60]+ "...")
    ranges["recent pages"] = arts
    subwins = {"recent pages":{"x":7,"y":12,"h":7,"w":68}}
    if isFirst:
        for opt in opts:
           if opt in ranges:
               opts[opt] = ranges[opt][0] if ranges[opt] else ""
    clear_screen(std)
    ch = 'a'
    mi = 0
    history = load_obj("history", "", [])
    while ch != 'q':
        ch, opts, mi = show_menu(opts, ranges, shortkeys = shortkeys, mi = mi, subwins= subwins)

        if type(ch) is int: 
            ch = chr(ch)
        url = ""
        if ch == 'l' or ch == "load":
            url = opts["address"]
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
                 show_err("error: " + str(e))
                 if ch == 'l' or ch == "load":
                     mi = 0
                 continue
             if not url in history:
                 history.append(url)
                 save_obj(history, "history", "")
             art = {"id":a.title,"pdfUrl":a.url, "title":a.title, "sections":[{"title":"all", "fragments":get_frags(a.text)},{"title":"summary", "fragments":[{"text":a.summary}]}]}
             if not art in recent_pages:
                 recent_pages.append(art)
                 save_obj(recent_pages, "recent_pages","")
             show_article(art)
        elif ch == "recent pages":
             selected = opts["recent pages"]
             if selected == "":
                 show_err("Please select articles to load")
             else:
                 articles = load_obj(selected, "websites")
                 if articles != None:
                     ret = list_articles(articles, "sel articles")
                 else:
                     show_err("Unable to load the file....")
    save_obj(opts, "web_opts", "")

def search():
    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    opts = None # load_obj("query_opts", "")
    isFirst = False
    if opts is None:
        isFirst = True 
        opts = {"keywords":"reading comprehension", "year":"","task":"", "conference":"", "dataset":"","sep1":"", "search":"button", "last results":"button"}
    ranges = {
            "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
            "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
            "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
            "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ],
            }
    if isFirst:
        for opt in opts:
           if opt in ranges:
               opts[opt] = ranges[opt][0] if ranges[opt] else ""
    clear_screen(std)
    ch = 'a'
    shortkeys = {"s":"search", "l":"last results"}
    mi = 0
    while ch != 'q':
        ch, opts, mi = show_menu(opts, ranges, shortkeys = shortkeys, mi = mi)
        if type(ch) is int: 
            ch = chr(ch)
        if ch != 'q':
            for k,v in opts.items():
                if k in filter_items and v and v != "All":
                    filters[k] = str(v)
            try:
                ret = ""
                if ch == 's' or  ch == 'search':
                    show_info("Getting articles...")
                    query = opts["keywords"]
                    articles,ret = request(0)
                    fid = opts["keywords"] + '_' + opts["year"] + '_1_' + opts["conference"] + '_' + opts["task"] + '_' + opts["dataset"]
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
    save_obj(opts, "query_opts", "")

if __name__ == "__main__":
    wrapper(main)
