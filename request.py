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
from termcolor import colored
import getch as gh
from utility import *
import curses as cur
from curses import wrapper
from pathlib import Path

from appdirs import *


appname = "NodReader"
appauthor = "App"

std = None
theme_opts = {}
theme_ranges = {}
conf = {}
nods = {}

TEXT_COLOR = 100
ITEM_COLOR = 101
CUR_ITEM_COLOR = 102
SEL_ITEM_COLOR = 103
TITLE_COLOR = 104
INFO_COLOR = 105
ERR_COLOR = 106
color_map = {
        "text-color":TEXT_COLOR, 
        "back-color":TEXT_COLOR, 
        "item-color":ITEM_COLOR, 
        "cur-item-color":CUR_ITEM_COLOR,
        "sel-item-color":SEL_ITEM_COLOR,
        "title-color":TITLE_COLOR,
        }
nod_color = {
        "okay?":242,
        "OK":148,
        "PASS":178,
        "Didn't get":218,
        "Interesting!":248,
        "So?":118,
        "Got it!":98,
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
    cur.init_pair(ERR_COLOR, cW, cR)

def save_obj(obj, name, directory):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    Path(folder).mkdir(parents=True, exist_ok=True)
    fname = folder + '/' + name + '.pkl'
    with open(folder + '/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name, directory):
    if directory != "":
        folder = user_data_dir(appname, appauthor) + "/" + directory
    else:
        folder = user_data_dir(appname, appauthor)
    fname = folder + '/' + name + '.pkl'
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return None 
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


def request(query, page = 1, size=40, filters = None):
     
    page = int(page)
    page -= 1

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

    return response.json()['searchResults']['results'],""
    

def show_results(articles, fid, mode = 'list'):

    global theme_opts, theme_ranges

    if len(articles) == 0:
        return "No article was loaded!"
    rows, cols = std.getmaxyx()
    ch = ''
    sels = load_obj("sels","")
    if sels is None:
        sels = {}
    start = 0
    sects_num = 0
    k,sc  = 0,0
    N = len(articles)
    ls = True
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
    if N == 0:
        return "No result fond!"
    bg = ""
    expand = 3
    new_art = True
    new_sect = True
    old_sc = -1 
    frags_text = ""
    art_id = -1
    si = 0
    fc = 0
    cury = 0
    nod = {}
    page_height = rows - 4
    scroll = 1
    while ch != ord('q'):
        # clear_screen(text_win)
        text_win.clear()
        start_row = max(0, start_row)
        start_row = min(cury - 1, start_row)
        if bg != theme_opts["back-color"]:
            clear_screen(main_win)
            bg = theme_opts["back-color"]
            text_win.refresh(start_row,0, 0,0, rows-1, cols)
        k = max(k, 0)
        k = min(k, len(articles) - 1)
        k = min(k, N-1)
        pos = {} 
        art = articles[k]
        if art["id"] != art_id:
           if art_id != 0 and nod:
               nods[art_id] = nod
               save_obj(nods, "nods", "")
           art_id = art['id']
           # with open(art_id + ".txt", "w") as ff:
           #    print(art, file = ff)
           if art_id in nods:
               nod = nods[art_id]
           else:
               nod = {}
           new_art = True
           new_sect = True
           old_sc = -1
           sc = 0
           fc = 0
           si = 0
           if nod:
               while si in nod and nod[si] != "okay?":
                   si += 1
           fsn = 0
           ffn = 0
           frags_sents = {}
           for b in art["sections"]:
               frags_text = ""
               b['frags_offset'] = ffn
               b["sents_offset"] = fsn
               for c in b['fragments']:
                   text = c['text']
                   if text.strip() == "":
                       del b["fragments"][c]
                   else:
                       sents = split_into_sentences(text)
                       frags_sents[ffn] = sents
                       c['sents_offset'] = fsn 
                       c['sents_num'] = len(sents)
                       fsn += len(sents)
                       ffn += 1
               b["sents_num"] = fsn - b["sents_offset"]
               b['frags_num'] = len(b["fragments"])
           total_sents = fsn 
           total_frags = ffn


        if sc != old_sc:
            new_sect = True
            old_sc = sc
        else: 
            new_sect = False
        if mode == 'd':
           a = art
           start_time = time.time()
           #clear_screen(text_win)
           text_win.clear()
           sn = 0
           sects_num = len(a["sections"])
           sc = max(sc, 0)
           sc = min(sc, sects_num)
           title = "\n".join(textwrap.wrap(a["title"], width)) # wrap at 60 characters
           top =  "["+str(k)+"] " + title
           mprint(top,  text_win, TITLE_COLOR, attr = cur.A_BOLD) 
           mprint("", text_win)
           fsn = 0
           ffn = 0
           for b in a["sections"]:
               fragments = b["fragments"]
               fnum = len(fragments)
               if sn == sc:
                   sect_fc = fc - b["frags_offset"]
                   sect_title = b["title"] + f"({sect_fc+1}/{fnum})" 
               else:
                   sect_title = b["title"]
               if art_id in sels and b["title"].lower() in sels[art_id]:
                   mprint(sect_title, text_win, SEL_ITEM_COLOR)
               else:
                   _color = CUR_ITEM_COLOR if sc == sn else ITEM_COLOR
                   mprint(sect_title, text_win, _color, attr = cur.A_BOLD)
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
                              frags_sents[ffn] = frag_sents
                          else:
                              frag_sents = frags_sents[ffn]

                          # if "level" in frag:
                             # color = frag["level"] % 250
                          hlcolor = SEL_ITEM_COLOR
                          if True:
                              for sent in frag_sents:
                                  feedback = nod[fsn] if fsn in nod else "0"
                                  f_color = SEL_ITEM_COLOR
                                  # f_color = nod_color[feedback]
                                  color = TEXT_COLOR
                                  sent = "\n".join(textwrap.wrap(sent, width -5))
                                  if fsn == si:
                                      mprint(sent, text_win, hlcolor, end= " ")
                                  else:
                                      mprint(sent, text_win, color, end=" ")
                                  mprint(feedback, text_win, f_color)
                                  pos[fsn],_ = text_win.getyx()
                                  fsn += 1
                          
                          mprint("\n", text_win, color)
                          ffn += 1
               sn += 1
        else:
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

                mprint(item, text_win, color)

        #print(":", end="", flush=True)
        cury, curx = text_win.getyx()
        if mode == 'd':
            sc = min(sc, sects_num)
            f_offset = art['sections'][sc]['frags_offset'] 
            fi = fc - f_offset + 1            
            offset = art["sections"][sc]["fragments"][fi - 1]["sents_offset"] 
            show_info("sc:"+ str(sc) + " start row:" + str(start_row) + " frag offset:"+ str(f_offset)  + " fc:" + str(fc) + " si:" + str(si) + " sent offset:" + str(offset) +  " pos[0]:"+str(pos[0]))
        if mode == 'd' and si in pos and not ch == ord('.') and not ch == ord(','):
            if pos[si] > 7:    
                start_row = pos[si] - 7 
            else:
                start_row = 0
        text_win.refresh(start_row,0, 2,5, rows -2, cols- 5)

        ch = get_key(std)
        # this will stop the timer

        clear_screen(win_info)
        if ch == ord('z'):
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
                save_obj(sel_arts, fid, "articles")
                articles = sel_arts
                show_info("Selected articles were saved as " + fid)

        if ch == ord('q') and mode == 'd':
            ch = 0
            start_row = 0
            mode = 'list'
            if art_id != 0 and nod:
               nods[art_id] = nod
               save_obj(nods, "nods", "")
        if ch == ord('x'):
            fast_read = not fast_read
        if ch == ord('f') or ch == ord('s'):
            add_remove_sels(sels, art, ch)
        if ch == ord('e') and mode == 'd':
            if expand < 3:
                expand += 1
        if ch == ord('c') and mode == 'd':
            if expand > 0:
                expand -= 1
        if ch == ord('a'):
            for ss in range(start,start+15):
                  rr = articles[ss]
                  add_remove_sels(sels, rr, 's')

        if ch == ord('s') and mode == 'd':
            cur_sect = art["sections"][sc]["title"].lower()
            if art_id in sels:
                if cur_sect in sels[art_id]:
                    sels[art_id].remove(cur_sect)
                else:
                    sels[art_id].append(cur_sect)
            else:
                sels[art_id] = [cur_sect]
        if ch == 127:
            start_row = 0
            mode = 'list'
            if art_id != 0 and nod:
               nods[art_id] = nod
               save_obj(nods, "nods", "")

        if mode == 'd' and (ch == cur.KEY_RIGHT or ch == cur.KEY_DOWN or chr(ch).isdigit()):
#            if chr(ch) == '0':
#                nod[si] = "So?"
#            elif ch == cur.KEY_RIGHT or chr(ch) == 'o' or chr(ch) == '1':
#                nod[si] = "OK"
#            elif chr(ch) == "2" or chr(ch) == 'p':
#                nod[si] = "PASS"
#            elif chr(ch) == "3":
#                nod[si] = "Interesting!"
#            elif chr(ch) == "4":
#                nod[si] = "Didn't get"
#            elif chr(ch) == "5":
#                nod[si] = "Got it!"
#            
            end_time = time.time()
            reading_time = end_time - start_time 
            nod[si] = str(reading_time)
            if si + 1 < total_sents:
                si += 1
            sents_num = art["sections"][sc]["fragments"][fi -1]["sents_num"] 
            if si > offset + sents_num - 1:
                fc += 1
        if mode == 'd' and (ch == cur.KEY_LEFT or ch == cur.KEY_UP):
            si -= 1
            if si < 0: 
                si = 0
            if si < offset:
                fc -= 1

        update_si = False
        if ch == ord('p'):
            if mode == 'd':
                k -= 1
        if ch == ord('n'):
            if mode == 'd':
                k += 1
            else:
                articles = request
        if ch == ord('k'):
            sc -= 1
            if sc >= 0:
                fc = art["sections"][sc]["frags_offset"]
                update_si = True
        if ch == ord('j'):
            sc += 1
            if sc < sects_num:
                fc = art["sections"][sc]["frags_offset"]
                update_si = True
        if ch == ord('l') and mode == 'd': 
                art["sections"][sc]["fragments"][fi -1]["level"] = random.randint(3, 9) 
                fc += 1
                update_si = True
        if ch == ord('h') and mode == 'd':
            if mode == 'd':
                fc -= 1
                update_si = True

        if ch == cur.KEY_DOWN:
            if mode == 'list':
                k +=1
        if ch == ord('.'):
            if start_row < cury:
                start_row += scroll
            else:
                cur.beep()

        if ch == cur.KEY_UP:
            if mode == 'list':
                k -= 1
        if ch == ord(','):
            if start_row > 0:
                start_row -= scroll
            else:
                cur.beep()

        if k >= start + 15:
            ch = cur.KEY_NPAGE
        if k < start:
            ch = "prev_pg"

        if ch == cur.KEY_PPAGE or ch == 'prev_pg':
            if mode == 'd': 
                si = max(si - 10, 0)
            else:
                start -= 15
                start = max(start, 0)
                k = start + 14 if ch == 'prev_pg' else start
        elif ch == cur.KEY_NPAGE:
            if mode == 'd':
                si = min(si + 10, total_sents -1)
            else:
                start += 15
                start = min(start, N - 15)
                k = start
        elif ch == cur.KEY_HOME:
            if mode == 'd':
                sc = 0
                fc = 0
                si = 0
            else:
                k = start
        elif ch == cur.KEY_END:
            if mode == 'd':
                si = total_sents -1 
                sc = sects_num -1
                fc = total_frags  -1
            else:
                k = start + 14

        if mode == 'd':
            sc = max(0, sc)
            sc = min(sc, sects_num - 1)
            f_offset = art["sections"][sc]["frags_offset"]
            frags_num = art["sections"][sc]["frags_num"]
            if fc < f_offset:
                if sc > 0:
                    sc -=1
                else:
                    sc = 0
                    fc = 0
                    cur.beep()
            elif fc >= f_offset + frags_num:
                if sc < sects_num - 1:
                    sc +=1
                else:
                    fc -= 1
                    cur.beep()
            if update_si:
                f_offset = art['sections'][sc]['frags_offset'] 
                fi = fc - f_offset             
                si = art["sections"][sc]["fragments"][fi]["sents_offset"] 

            art['sections'][sc]['fc'] = fc 
        if ch == cur.KEY_ENTER or ch == 10:
                mode = 'd'
                fc = 0
                sc = 0
        if ch == ord('t'):
            info = "s) save as   d) delete"
            _, theme_opts = show_menu(theme_opts, theme_ranges, "::Settings", info = info)
            save_obj(theme_opts, conf["theme"], "themes")
        if ch == ord('w') or ch == ord('m'):
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
    return "" 

def refresh_menu(opts, menu_win, sel, ranges):
    global clG
    clear_screen(menu_win)
    row = 3 
    col = 5
    gap = col + 15
    for k, v in opts.items():
       colon = ":" # if not k in ranges else ">"
       if k == sel:
           if k == "sep":
               print_there(row, col,  str(v) + colon,  menu_win, CUR_ITEM_COLOR)
           else:
               print_there(row, col, "{:<15}".format(k), menu_win, CUR_ITEM_COLOR, attr = cur.A_BOLD)
               print_there(row, gap, colon, menu_win, CUR_ITEM_COLOR, attr = cur.A_BOLD)
       else:
           if k == "sep":
               print_there(row, col,  str(v) + colon, menu_win, TITLE_COLOR)
           else:
               print_there(row, col, "{:<15}".format(k), menu_win, ITEM_COLOR, attr = cur.A_BOLD)
               print_there(row, gap, colon, menu_win, ITEM_COLOR, attr = cur.A_BOLD)

       if "color" in k:
           print_there(row, col + 17, "{:^5}".format(str(v)), menu_win, color_map[k]) 
       elif k != "sep":
           print_there(row, col + 17, "{}".format(v), menu_win, TEXT_COLOR)

       row += 1

def get_sel(opts, mi):
    mi = max(mi, 0)
    mi = min(mi, len(opts)-1)
    return list(opts)[mi], mi

win_info = None
def show_info(msg, color=INFO_COLOR):
    global win_info
    rows, cols = std.getmaxyx()
    win_info = cur.newwin(1, cols, rows-1,0) 
    win_info.bkgd(' ', cur.color_pair(color)) # | cur.A_REVERSE)
    win_info.erase()
    print_there(0,1," {} ".format(msg), win_info, color)
    win_info.clrtoeol()

def show_msg(msg, color=INFO_COLOR):
   show_info(msg, color)

def show_err(msg, color=ERR_COLOR):
    show_msg(msg, color)
    win_info.getch()

def load_preset(new_preset):
    opts = load_obj(new_preset,"themes")
    if opts == None:
        dark ={'preset': 'dark', 'text-color': '250', 'back-color': '234', 'item-color': '65', 'cur-item-color': '101', 'sel-item-color': '148', 'title-color': '28'}
        light = {'preset': 'light', 'text-color': '32', 'back-color': '253', 'item-color': '12', 'cur-item-color': '35', 'sel-item-color': '39', 'title-color': '28'}
        save_obj(dark, "dark", "themes")
        save_obj(light, "light", "themes")
        theme_ranges["preset"].append("dark")
        theme_ranges["preset"].append("light")
        new_preset = "dark"
        opts = dark

    opts["preset"] = new_preset
    reset_colors(opts)
    conf["theme"] = new_preset
    save_obj(conf, "conf", "")
    return opts

def show_menu(opts, ranges, shortkeys = [], title = "::NodReader v1.0", info = ""):
    mi = 0
    si = 0
    ch = 'a'
    mode = 'm'

    rows, cols = std.getmaxyx()
    height = rows -1  
    width = cols 

    menu_win = cur.newwin(height, width, 0, 0)
    sub_menu_win = menu_win.subwin(5, width//2 + 5)

    menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)
    sub_menu_win.bkgd(' ', cur.color_pair(TEXT_COLOR)) # | cur.A_REVERSE)

    mprint(title.center(rows), menu_win)
    hide_cursor()
    _help = False
    last_preset = conf["theme"]
    
    row = 3 
    col = 5
    mt, st = "", ""
    while ch != ord('q'):
        clear_screen(sub_menu_win)
        if info != "":
            show_info(info)
        sel,mi = get_sel(opts, mi)
        if mode == 'm':
            refresh_menu(opts, menu_win, sel, ranges)
        if mode == 's':
           if sel not in ranges:
              # opts[sel]=""
              refresh_menu(opts, menu_win, sel, ranges)
              val = minput(menu_win,row + mi, col, "{:<15}".format(sel) + ": ") 
              if val != "<ESC>":
                  opts[sel] = val
              mi += 1
              sel,mi = get_sel(opts, mi)
              refresh_menu(opts, menu_win, sel, ranges)
              mode = 'm'
              mt = ""
           else:
              si = min(si, len(ranges[sel]) - 1)
              si = max(si, 0)
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

        if _help:
            _help = False
            clear_screen(menu_win)
            fname = "ReadMe.md"
            obj_file = Path(fname) 
            if not obj_file.is_file():
                cont = "ReadMe is missing! please refer to the project address on github..."
            else:
                with open("ReadMe.md", "r") as f:
                    cont = f.read()
            mprint(cont, menu_win)
            show_info("Press any key to return ...")
            a = std.getch()
            refresh_menu(opts, menu_win, sel, ranges)
            if info != "":
                show_info(info)
            ch = 'a'
        ch = get_key(std)
            
        if ch == ord("h"):
            _help = not _help
        elif ch == cur.KEY_DOWN:
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
            if sel in ranges:
                si = min(si, len(ranges[sel]) - 1)
                si = max(si, 0)
            if sel == "sep":
                mi += 1
            elif mode == 'm':
                mode = 's'
                st = ""
                if sel in ranges:
                    si = ranges[sel].index(opts[sel])
            elif mode == 's':
                opts[sel] = ranges[sel][si]
                if "preset" in opts:
                    reset_colors(opts)
                if sel == "text files":
                    ch = ord('p')
                    return ch, opts
                elif sel == "saved articles":
                    ch = ord('o')
                    return ch, opts
                elif sel == "last results":
                    ch = ord('l')
                    return ch, opts
                elif sel == "preset":
                    save_obj(opts, last_preset, "themes")
                    new_preset = ranges[sel][si]
                    opts = load_preset(new_preset)
                    last_preset = new_preset
                    refresh_menu(opts, menu_win, sel, ranges)
                    show_info(new_preset +  " was loaded")

                mode = 'm'    
                mt = ""
                si = 0
        elif ch == cur.KEY_RIGHT:
            if sel == "sep":
                mi += 1
            else:
                mode = 's'
                st = ""
                if sel in ranges:
                    si = ranges[sel].index(opts[sel])
        elif ch == cur.KEY_LEFT or ch == 27:
            mode = 'm'
            mt = ""
        elif ch == ord('q'):
            # show_cursor()
            break;
        elif ch == ord('d') and "preset" in opts:
            confirm = minput(win_info, 0, 1, "Are you sure you want to delete " + opts["preset"] + "? (y/n)")
            if confirm == "y" or confirm == "Y":
                del_obj(opts["preset"], "themes")
                ranges["preset"].remove(opts["preset"])
                new_preset = ranges["preset"][0] if len(ranges["preset"]) > 0 else "dark"
                opts = load_preset(new_preset)
                last_preset = new_preset
                refresh_menu(opts, menu_win, sel, ranges)
                show_info(new_preset +  " was loaded")

        elif ch == ord('s') and "preset" in opts:
            fname = minput(win_info, 0, 1, "Save as:") 
            if fname != "<ESC>":
                save_obj(opts, fname, "themes")
                reset_colors(opts)
                show_info(opts["preset"] +  " was saved as " + fname)
                opts["preset"] = fname
                ranges["preset"].append(fname)
                refresh_menu(opts, menu_win, sel, ranges)
        elif chr(ch) in shortkeys:
            mi = list(opts.keys()).index(shortkeys[chr(ch)])
            mode = 's'
            st = ""
        elif ch == ord('r') or ch == ord('l'): 
            return ch, opts
        else:
            if mode == 's' and chr(ch).isdigit() and sel in ranges:
                si,st = find(ranges[sel], st, chr(ch), si)
            else:
                cur.beep()
    return ch, opts

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

    global theme_ranges, theme_opts, std, conf, nods

    std = stdscr
    cur.start_color()
    cur.use_default_colors()

    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    opts = None # load_obj("query_opts")
    if opts is None:
        opts = {"search":"reading comprehension", "year":"","task":"", "conference":"", "dataset":"", "sep":"","last results":"", "saved articles":"","sep":"", "text files":""}
    ranges = {
            "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
            "page":[str(y) for y in range(1,100)],
            "page-size":[str(y) for y in range(30,100,10)], 
            "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
            "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
            "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ],
            "last results":["None"],
            "saved articles":["None"],
            "text files":["None"],
            }

    last_results_file = user_data_dir(appname, appauthor) + "/last_results.pkl"
    obj_file = Path(last_results_file) 
    if not obj_file.is_file():
        ranges["last results"] =["None"] 
    else:
        cr_time = time.ctime(os.path.getmtime(last_results_file))
        cr_date = datetime.datetime.strptime(str(cr_time), "%a %b %d %H:%M:%S %Y")
        ranges["last results"] = [cr_date]


    data_dir = user_data_dir(appname, appauthor) + "/articles"

    saved_articles =  [Path(f).stem for f in Path(data_dir).glob('*') if f.is_file()]
    if not saved_articles:
        ranges["saved articles"] =["None"] 
    else:
        ranges["saved articles"] = saved_articles

    text_files =  [Path(f).name for f in Path(".").glob('*.txt') if f.is_file()]
    if not text_files:
        ranges["text files"] =["None"] 
    else:
        ranges["text files"] = text_files
    for opt in opts:
       if opt in ranges:
           opts[opt] = ranges[opt][0]
    conf = load_obj("conf", "")
    if conf is None:
        conf = {"theme":"default"}
    nods = load_obj("nods", "")
    if nods is None:
        nods = {}

    colors = [str(y) for y in range(-1, cur.COLORS)]
    theme_ranges = {
            "preset":[],
            "text-color":colors,
            "back-color":colors,
            "item-color":colors,
            "cur-item-color":colors,
            "sel-item-color":colors,
            "title-color":colors,
            }

    theme_opts = load_preset(conf["theme"]) 
    # mprint(str(theme_opts),std)
    # std.getch()

    themes_dir = user_data_dir(appname, appauthor) + "/themes"
    saved_themes =  [Path(f).stem for f in Path(themes_dir).glob('*') if f.is_file()]
    if not saved_themes:
        theme_ranges["preset"] =["default"] 
    else:
        theme_ranges["preset"] = saved_themes

    reset_colors(theme_opts)
    #os.environ.setdefault('ESCDELAY', '25')
    #ESCDELAY = 25
    clear_screen(std)
    choice = ord('a')
    shortkeys = {"y":"year", "o":"saved articles", 'p':"text files"}
    while choice != ord('q'):
        info = "s) search l) last results o) saved articles  h) help  q) quit"
        
        choice, opts = show_menu(opts, ranges, shortkeys = shortkeys, info = info)
        ch = chr(choice)
        save_obj(opts, "query_opts", "")
        if ch in ['l', 'o', 's', 'r','p']:
            for k,v in opts.items():
                if k in filter_items and v and v != "All":
                    filters[k] = str(v)
            try:
                ret = ""
                if ch == 'r':
                    show_info("Getting articles...")
                    articles,ret = request(opts["search"], 1, 15 , filters)
                    fid = opts["search"] + '_' + opts["year"] + '_1_' + opts["conference"] + '_' + opts["task"] + '_' + opts["dataset"]
                    fid = fid.replace(' ','_')
                    fid = fid.replace('__','_')
                    fid = fid.replace('__','_')
                    if len(articles) > 0 and ret == "":
                        save_obj(articles, "last_results", "")
                        ret = show_results(articles, fid)
                elif ch == 'p':
                    text = opts["text files"]
                    with open(text, "r") as f:
                        data = f.read()
                    art = [{"id":text, "title":text, "sections":[{"title":"all", "fragments":[{"text":data}]}]}]
                    ret = show_results(art, text, mode = 'd')
                elif ch == 'l':
                     articles = load_obj("last_results", "")
                     if articles != None:
                         ret = show_results(articles, "last_results")
                     else:
                         show_err("Last results is missing....")
                elif ch == 'o':
                     selected = opts["saved articles"]
                     if selected == None:
                         show_err("Please select articles to load")
                     else:
                         articles = load_obj(selected, "articles")
                         if articles != None:
                             ret = show_results(articles, "sel articles")
                         else:
                             show_err("Unable to load the file....")

                if ret:
                    mprint(ret, std)
                    std.getch()

            except KeyboardInterrupt:
                choice = ord('q')
                show_cursor()

if __name__ == "__main__":
    wrapper(main)
