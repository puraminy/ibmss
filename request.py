#v2 tehran
import requests
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
import platform

from pdf2text import *

appname = "NodReader"
appauthor = "App"

std = None
theme_opts = {}
theme_ranges = {}
conf = {}

cW = 0
cR = 2
cG = 3
cY = 4
cB = 5
cPink = 14
cC = 7
clC = 15
clY = 12
cGray = 9
clGray = 249
clG = 11
cllC = 82
cO = 209
cW_cB = 250

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

# Add or remove an item from the list of selected sections of articles
def toggle_in_list(d, art, ch):
    key = art["id"] # article id
    sects = 'abstract introduction conclusion'
    if not key in d:
        if ch == ord('s'):
           d[key] = sects.split(' ')
        else:
           d[key] = [s["title"].lower() for s in art["sections"]]
    else: 
        del d[key]


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
        return ("Http Error:" + str(errh))
    except requests.exceptions.ConnectionError as errc:
        return ("Error Connecting:" + str(errc))
    except requests.exceptions.Timeout as errt:
        return ("Timeout Error:" + str(errt))
    except requests.exceptions.RequestException as err:
        return ("OOps: Something Else" + str(err))

    articles = response.json()['searchResults']['results']
    conference = ''
    if "conference" in filters:
        conference = filters['conference']
    task = ''
    if "task" in filters:
        task = filters['task']
    dataset = ''
    if "dataset" in filters:
        dataset = filters['dataset']
    year = ''
    if "year" in filters:
        year = filters['year']
    fid = query + '_' + str(year) + '_' + str(page) + '_' + conference + '_' + task + '_' + dataset
    fid = fid.replace(' ','_')
    fid = fid.replace('__','_')
    fid = fid.replace('__','_')

    save_obj(articles, "last_results", "")

    return show_results(articles, fid)

def show_results(articles, fid):
    clear_screen(std)
    rows, cols = std.getmaxyx()
    ch = ''
    sels = {}
    start = 0
    sects_num,frags_num = 0,0
    k,fc,sc  = 0,0,0
    N = len(articles)
    mode = 'list'
    ls = True
    fast_read = False
    text_win = cur.newwin(rows - 5, cols - 5, 2, 5)
    main_win = cur.newwin(rows -1, cols, 0, 0)
    mprint(str(articles[0]))
    width = cols - 10
    # text_win = std
    if N == 0:
        return "No result fond!"
    bg = ""
    while ch != ord('q'):
        text_win.bkgd(' ', cur.color_pair(int(theme_opts["background-color"])))
        main_win.bkgd(' ', cur.color_pair(int(theme_opts["background-color"])))
        clear_screen(text_win)
        if bg != theme_opts["background-color"]:
            bg = theme_opts["background-color"]
            clear_screen(main_win)
        k = max(k, 0)
        k = min(k, len(articles) - 1)
        k = min(k, N-1)
        art = articles[k]
        art_id = art['id']
        if mode == 'd':
           a = art
           clear_screen(text_win)
           sn = 0
           sects_num = len(a["sections"])
           sc = max(sc, 0)
           sc = min(sc, sects_num)
           title = "\n".join(textwrap.wrap(a["title"], width)) # wrap at 60 characters
           top =  "["+str(k)+"] " + title
           mprint(top,  text_win, int(theme_opts["title-color"])) 
           for b in a["sections"]:
               if sn != sc:
                   sect_title = b["title"]
                   if art_id in sels and b["title"].lower() in sels[art_id]:
                       # print_there(sn,0, b["title"], sect_win, 7)
                       mprint("*" +sect_title, text_win, int(theme_opts["sel-sect-color"]), cur.A_BOLD)
                   else:
                       # print_there(sn, 0, b["title"], sect_win, 10)
                       mprint(sect_title, text_win, int(theme_opts["head-color"]), cur.A_BOLD)
               else:
                   frags_num = len(b['fragments'])
                   frags_text = ""
                   for c in b['fragments']:
                       frags_text += '\n\n' + c['text']
                   if False: #fast_read:
                       words = frags_text.split()                
                       for word in words:
                          print_there(20, 40, colored(word + ' '.join([10*' ']), 'green') + cend, std)
                          sleep(len(word)*0.05)
                   sents = split_into_sentences(frags_text)    
                   frags_num = len(sents)
                   sect_title = b["title"] + f"({fc+1}/{frags_num})" 
                   if art_id in sels and b["title"].lower() in sels[art_id]:
                       # print_there(sn,0, sect_title, sect_win, 7)
                       mprint("*"+sect_title, text_win, int(theme_opts["sel-sect-color"]))
                   else:
                       # print_there(sn,0, sect_title, sect_win, 10)
                       mprint(sect_title, text_win, int(theme_opts["sel-head-color"]), True)
                   # mprint(frags_text, text_win, 4)
                   for fn, text in enumerate(sents):
                       if fn == fc:
                          frag = "\n".join(textwrap.wrap(text, width - 4))
                          frag =  textwrap.indent(frag, " "*2) 
                          mprint(frag, text_win, int(theme_opts["text-color"]))
                          # print_there(0,0, frag, text_win, 3)


               sn += 1
        else:
            for j,a in enumerate(articles[start:start + 15]): 
                i = start + j
                paper_title =  a['title']
                dots = ""
                if len(paper_title) > width - 10:
                   dots = "..."
                item = "{}{} {}".format(i, ":", paper_title[:width - 10] + dots)               
                color = int(theme_opts["text-color"])
                if a["id"] in sels:
                    color = int(theme_opts["sel-sect-color"])
                if i == k:
                    color = cG

                mprint(item, text_win, color)

        #print(":", end="", flush=True)
        ch = get_key(std)
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
            mode = 'list'
        if ch == ord('x'):
            fast_read = not fast_read
        if ch == ord('f') or ch == ord('s'):
            toggle_in_list(sels, art, ch)

        if ch == ord('a'):
            for ss in range(start,start+15):
                  rr = articles[ss]
                  toggle_in_list(sels, rr, 's')

        if ch == ord('c') and mode == 'd':
            cur_sect = art["sections"][sc]["title"].lower()
            if art_id in sels:
                if cur_sect in sels[art_id]:
                    sels[art_id].remove(cur_sect)
                else:
                    sels[art_id].append(cur_sect)
            else:
                sels[art_id] = [cur_sect]
        if ch == ord('p'):
            k-=1
        if ch == ord(":"):
            cmd = get_cmd()
            
            if len(cmd) == 1:
                command = cmd[0].strip()
                if len(command) == 1:
                    ch = command
                elif command != "set":
                    show_err("Unknown command:" + command)
            else:
                command = cmd[0].strip()
                arg = cmd[1].strip()
                if command == "w" or command == "write":
                    fid = arg
                    ch = ord("w")
                elif command != "set":
                    show_err("Unknown command:" + command)
        if ch == ord('n'):
            k+=1
        if ch == cur.KEY_RIGHT and mode == 'd': 
                fc += 1
        if ch == ord('l') or ch == 127:
            mode = 'list'
        if ch == ord('d') or ch == cur.KEY_RIGHT or ch == 10 or ch == 9:
            if mode == 'list':
                mode = 'd'
                fc = 0
                sc = 0
        elif ch == cur.KEY_LEFT:
            if mode == 'd':
                fc -= 1
        elif ch == cur.KEY_UP:
            if mode == 'd': 
                sc -= 1
                fc = 0
            else:
                k -=1
        elif ch == cur.KEY_DOWN:
            if mode == 'd':
                sc += 1
                fc = 0
            else:
                k +=1
        elif ch == cur.KEY_HOME:
            if mode == 'd':
                sc = 0
                fc = 0
            else:
                k = start
        elif ch == cur.KEY_END:
            if mode == 'd':
                sc = sects_num
                fc = 0
            else:
                k = start + 14

        if mode == 'd':
            if fc < 0:
                fc = 0
                if sc > 0:
                    sc -=1
                else:
                    mode = 'list'
            elif fc >= frags_num:
                fc = 0
                if sc < sects_num - 1:
                    sc +=1
                else:
                    k +=1
                    sc = 0
        if k >= start + 15:
            ch = cur.KEY_NPAGE
        if k < start:
            ch = "prev_pg"
        if ch == cur.KEY_NPAGE:
            if mode == 'list':
                start += 15
                start = min(start, N - 15)
                k = start
            else:
                k +=1
        if ch == cur.KEY_PPAGE or ch == 'prev_pg':
            if mode == 'list':
                start -= 15
                start = max(start, 0)
                k = start + 14 if ch == 'prev_pg' else start
            else:
                k -= 1
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

def get_cmd():

    global theme_opts, theme_ranges
    rows, cols = std.getmaxyx()
    win = cur.newwin(1, cols, rows-1, 0) 
    cmd = minput(win, 0, 0, ":")
    # cmd = re.split(r'\s(?=")', cmd) 
    cmd = shlex.split(cmd)
    if len(cmd) == 0:
        return ['<Enter>']
    if len(cmd) == 1:
        command = cmd[0]
        if command == "set":
            _, theme_opts = show_menu(theme_opts, theme_ranges, "::Settings")
            save_obj(theme_opts, conf["theme"], "themes")
            return cmd
        else:
            return cmd
 
    command = cmd[0].strip()
    arg = cmd[1].strip()
    if command != "set":
        return cmd
    else:
        apply_settings(arg, theme_opts, theme_ranges, win)
        return cmd

def apply_settings(arg, opts, ranges, win):
    arg = arg.split('=')
    if len(arg) == 1:
        show_err("use 'set opt=val' to set an option, press any key ...")
    else:
        key = arg[0].strip()
        val = arg[1].strip()
        if key not in opts:
            show_err(key + " is an invalid option, press any key...")
        else:
           mi = list(opts.keys()).index(key)
           if key not in ranges:
               opts[key] = val
           else:
                if val in ranges[key]:
                    opts[key] = val
                else:
                    show_err(val + " is invalid for " + key + ", press any key ...")

def refresh_menu(opts, menu_win, sel):
    global clG
    clear_screen(menu_win)
    row = 0
    for k, v in opts.items():
       if k == sel:
           if k == "sep":
               print_there(row, 0,  str(v) + ":", menu_win, cO)
           else:
               print_there(row, 0, "{:<15}> ".format(k), menu_win, cO)
       else:
           if k == "sep":
               print_there(row, 0,  str(v) + ":", menu_win, cG)
           else:
               print_there(row, 0, "{:<15}: ".format(k), menu_win, cB)

       if "color" in k:
           print_there(row, 17, "{}".format(str(v)), menu_win, int(v), cur.A_UNDERLINE) 
       elif k != "sep":
           print_there(row, 17, "{}".format(v), menu_win, cW)

       row += 1

def get_sel(opts, mi):
    mi = max(mi, 0)
    mi = min(mi, len(opts)-1)
    return list(opts)[mi], mi

win_info = None
def show_info(msg, color=501):
    global win_info
    rows, cols = std.getmaxyx()
    win_info = cur.newwin(1, cols, rows-1,0) 
    clear_screen(win_info)
    print_there(0,1, msg, win_info, color)

def show_msg(msg, color=cG):
   show_info(msg, color)

def show_err(msg, color=266):
    show_msg(msg, color)

def show_menu(opts, ranges, shortkeys = [], title = "::NodReader v1.0", info = ""):
    mi = 0
    si = 0
    ch = 'a'
    mode = 'm'

    rows, cols = std.getmaxyx()
    height = rows - 5
    width = cols - 10
    main_win = cur.newwin(rows -1, cols, 0, 0)

    clear_screen(main_win)
    menu_win = cur.newwin(height, width, 3, 5)
    sub_menu_win = menu_win.subwin(5, width//2 + 5)

    print_there(1, 0, title.center(80), std)
    hide_cursor()
    _help = False
    last_preset = conf["theme"]
    while ch != ord('q'):
        clear_screen(sub_menu_win)
        if info != "":
            show_info(info)
        sel,mi = get_sel(opts, mi)
        refresh_menu(opts, menu_win, sel)
        if mode == 's':
           if sel not in ranges:
              opts[sel]=""
              refresh_menu(opts, menu_win, sel)
              val = minput(menu_win, mi + 0, 0, "{:<15}".format(sel) + ": ") 
              opts[sel] = val
              mi += 1
              sel,mi = get_sel(opts, mi)
              refresh_menu(opts, menu_win, sel)
              mode = 'm'
           else:
              start = si - 5
              start = max(start, 0)
              if len(ranges[sel]) > 10:
                  start = min(start, len(ranges[sel])-10)
              if start > 0:
                  mprint("...", sub_menu_win, cW)
              for vi, v in enumerate(ranges[sel][start:start+10]):
                if start + vi == si:
                    if "color" in sel:
                       mprint(str(v) + " SSSS", sub_menu_win, int(v), cur.A_UNDERLINE) 
                    else:
                       mprint(str(v),sub_menu_win, cO)
                else:
                    if "color" in sel:
                       mprint(str(v) + " MMMM", sub_menu_win, int(v)) 
                    else:
                       mprint(str(v), sub_menu_win, cC)
              if start + 10 < len(ranges[sel]):
                  mprint("...", sub_menu_win, cW)

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
            refresh_menu(opts, menu_win, sel)
            if info != "":
                show_info(info)
            ch = 'a'
        ch = get_key(std)
        
        if ch == ord(':'):
            cmd = get_cmd()
            
        if ch == ord("h"):
            _help = not _help
        if ch == cur.KEY_DOWN:
            if mode == "m":
                mi += 1
            elif sel in ranges:
                si += 1
        if ch == cur.KEY_UP:
            if mode == "m":
                mi -= 1
            elif sel in ranges:
                si -= 1
        if ch == cur.KEY_NPAGE:
            if mode == "m":
                mi += 10
            elif sel in ranges:
                si += 10
        if ch == cur.KEY_PPAGE:
            if mode == "m":
                mi -= 10
            elif sel in ranges:
                si -= 10

        if sel in ranges:
            si = min(si, len(ranges[sel]) - 1)
            si = max(si, 0)
        if  ch == cur.KEY_ENTER or ch == 10 or ch == 13:
            if sel == "sep":
                mi += 1
            elif mode == 'm':
                mode = 's'
                if sel in ranges:
                    si = ranges[sel].index(opts[sel])
            elif mode == 's':
                opts[sel] = ranges[sel][si]
                if sel == "pdf files":
                    ch = ord('p')
                    return ch, opts
                elif sel == "saved articles":
                    ch = ord('o')
                    return ch, opts
                elif sel == "preset":
                    save_obj(opts, last_preset, "themes")
                    new_preset = ranges[sel][si]
                    tmp_opts = load_obj(new_preset,"themes")
                    if tmp_opts != None:
                        opts = tmp_opts
                        opts["preset"] = new_preset
                        last_preset = new_preset
                        conf["theme"] = new_preset
                        save_obj(conf, "conf", "")
                        refresh_menu(opts, menu_win, sel)
                        show_info(new_preset +  " was loaded")
                    else:
                        show_err("The file is missing")

                mode = 'm'    
                si = 0
        if ch == cur.KEY_RIGHT:
            if sel == "sep":
                mi += 1
            else:
                mode = 's'
                if sel in ranges:
                    si = ranges[sel].index(opts[sel])
        elif ch == cur.KEY_LEFT:
            mode = 'm'
        if ch == ord('q'):
            # show_cursor()
            break;
        if ch == ord('s') and "preset" in opts:
            fname = minput(win_info, 0, 0, "Save as:") 
            save_obj(opts, fname, "themes")
            show_info(opts["preset"] +  " was saved as " + fname)
            opts["preset"] = fname
            refresh_menu(opts, menu_win, sel)
        elif chr(ch) in shortkeys:
            mi = list(opts.keys()).index(shortkeys[chr(ch)])
            mode = 's'
        elif ch == ord('r') or ch == ord('l'): 
            return ch, opts
    return ch, opts


def main(stdscr):

    global theme_ranges, theme_opts, std, conf

    std = stdscr

    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    opts = None # load_obj("query_opts")
    if opts is None:
        opts = {"search":"reading comprehension", "year":"","page":1,"page-size":30,"task":"", "conference":"", "dataset":"", "sep":"","last results":"", "saved articles":"","sep":"", "pdf files":""}
    ranges = {
            "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
            "page":[str(y) for y in range(1,100)],
            "page-size":[str(y) for y in range(30,100,10)], 
            "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
            "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
            "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ],
            "last results":["None"],
            "saved articles":["None"],
            "pdf files":["None"],
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

    pdf_files =  [Path(f).name for f in Path(".").glob('*.pdf') if f.is_file()]
    if not pdf_files:
        ranges["pdf files"] =["None"] 
    else:
        ranges["pdf files"] = pdf_files
    for opt in opts:
       if opt in ranges:
           opts[opt] = ranges[opt][0]
    cur.start_color()
    cur.use_default_colors()
    c = 1
    for i in range(0, cur.COLORS):
        cur.init_pair(c, i, -1)
        c += 1
    for i in range(0, cur.COLORS):
        cur.init_pair(c, i, 0)
        c += 1


    conf = load_obj("conf", "")
    if conf is None:
        conf = {"theme":"default"}

    theme_opts = load_obj(conf["theme"], "themes")
    colors = [str(y) for y in range(510)]
    if theme_opts is None:
        theme_opts = {
                "preset":"default",
                "text-color":'246', 
                "background-color":'310',
                "head-color": str(cGray),
                "sel-head-color": str(clGray),
                "sel-sect-color": '266',
                "title-color":'300',
                }


    theme_ranges = {
            "preset":["default", "preset3"],
            "text-color":colors,
            "background-color":colors,
            "head-color":colors,
            "sel-head-color":colors,
            "sel-sect-color":colors,
            "title-color":colors,
            }

    themes_dir = user_data_dir(appname, appauthor) + "/themes"
    saved_themes =  [Path(f).stem for f in Path(themes_dir).glob('*') if f.is_file()]
    if not saved_themes:
        theme_ranges["preset"] =["default"] 
    else:
        theme_ranges["preset"] = saved_themes

    clear_screen(std)
    choice = ord('a')
    shortkeys = {"y":"year", "o":"saved articles", "p":"pdf files"}
    while choice != ord('q'):
        info = "s) search l) last results o) saved articles  h) help  q) quit"
        
        choice, opts = show_menu(opts, ranges, shortkeys = shortkeys, info = info)
        ch = chr(choice)
        save_obj(opts, "query_opts", "")
        if ch in ['l', 'o', 's', 'r', 'p']:
            for k,v in opts.items():
                if k in filter_items and v and v != "All":
                    filters[k] = str(v)
            clear_screen(std)
            try:
                ret = ""
                if ch == 'r':
                    show_info("Getting articles...")
                    ret = request(opts["search"], opts["page"], opts["page-size"], filters)
                elif ch == 'p':
                    pdf = opts["pdf files"]
                    data = pdfparser(pdf)
                    art = [{"id":pdf, "title":pdf, "sections":[{"title":"all", "fragments":[{"text":data}]}]}]
                    ret = show_results(art, pdf)
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
