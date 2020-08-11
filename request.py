#v2 tehran
import requests
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

def save_obj(obj, name ):
    folder = user_data_dir(appname, appauthor)
    Path(folder).mkdir(parents=True, exist_ok=True)
    fname = folder + '/' + name + '.pkl'
    with open(folder + '/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    folder = user_data_dir(appname, appauthor)
    fname = folder + '/' + name + '.pkl'
    obj_file = Path(fname) 
    if not obj_file.is_file():
        return None 
    with open(fname, 'rb') as f:
        return pickle.load(f)

def toggle_in_list(d, art, ch):
    key = art["id"]
    sects = 'abstract introduction conclusion'
    if not key in d:
        if ch == ord('s'):
           d[key] = sects.split(' ')
        else:
           d[key] = [s["title"].lower() for s in art["sections"]]
    else: 
        del d[key]

def request(std, query, page = 1, size=40, filters = None):
     
    page = int(page)
    page -= 1

    clear_screen(std)
    opts = load_obj("art_opts")
    if opts is None:
        opts = {"output":"","text-color":246, "head-color":cGray, "merge":True}
    ranges = {"text-color":[str(y) for y in range(255)]}
    inds = load_obj("art_inds")
    if inds is None:
        inds = {}

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
    rows, cols = std.getmaxyx()
    win_help = cur.newwin(1, cols, rows-1,0) 
    show_info("Getting articles...", win_help)
    try:
        response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)
    except requests.exceptions.HTTPError as errh:
        show_err("Http Error:" + str(errh), std)
    except requests.exceptions.ConnectionError as errc:
        show_err("Error Connecting:" + str(errc), std)
    except requests.exceptions.Timeout as errt:
        show_err("Timeout Error:" + str(errt), std)
    except requests.exceptions.RequestException as err:
        show_err("OOps: Something Else" + str(err), std)

    clear_screen(std)
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
    folder = query + '_' + str(year) + '_' + str(page) + '_' + conference + '_' + task + '_' + dataset
    folder = folder.replace(' ','_')
    folder = folder.replace('__','_')
    folder = folder.replace('__','_')

    articles = response.json()['searchResults']['results']
    ch = ''
    sels = {}
    start = 0
    sects_num,frags_num = 0,0
    k,fc,sc  = 0,0,0
    N = len(articles)
    mode = 'list'
    ls = True
    fast_read = False
    cend = '\x1b[0m'
    cend2 = '\033[0m'
    cgray = '\033[90m'
    begin_x = 10; begin_y = 1 
    height = 4; width = 80
    text_win = cur.newwin(rows - 5, cols - 5, 2, 5)
    width = cols - 10
    # text_win = std
    if N == 0:
        return "No result fond!"
    while ch != ord('q'):
        clear_screen(text_win)
        k = max(k, 0)
        k = min(k, len(articles) - 1)
        k = min(k, size-1)
        art = articles[k]
        art_id = art['id']
        if mode == 'd':
           a = art
           clear_screen(std)
           sn = 0
           sects_num = len(a["sections"])
           sc = max(sc, 0)
           sc = min(sc, sects_num)
           title = "\n".join(textwrap.wrap(a["title"], width)) # wrap at 60 characters
           top =  "["+str(k)+"] " + title
           mprint(top,  text_win, cC) 
           for b in a["sections"]:
               if sn != sc:
                   sect_title = b["title"]
                   if art_id in sels and b["title"].lower() in sels[art_id]:
                       # print_there(sn,0, b["title"], sect_win, 7)
                       mprint(sect_title, text_win, cW_cB, True)
                   else:
                       # print_there(sn, 0, b["title"], sect_win, 10)
                       mprint(sect_title, text_win, cGray, True)
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
                       mprint(sect_title, text_win, cW_cB)
                   else:
                       # print_there(sn,0, sect_title, sect_win, 10)
                       mprint(sect_title, text_win, int(opts["head-color"]), True)
                   # mprint(frags_text, text_win, 4)
                   for fn, text in enumerate(sents):
                       if fn == fc:
                          frag = "\n".join(textwrap.wrap(text, width - 4))
                          frag =  textwrap.indent(frag, " "*2) 
                          mprint(frag, text_win, int(opts["text-color"]))
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
                color = 0
                if a["id"] in sels:
                    color = cC
                if i == k:
                    color = cG

                mprint(item, text_win, color)

        #print(":", end="", flush=True)
        ch = get_key(std)
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
            cmd = get_cmd(opts, ranges, inds, win_help)
            save_obj(opts, "art_opts")
            save_obj(inds, "art_inds")
            
            if len(cmd) == 1:
                command = cmd[0].strip()
                if len(command) == 1:
                    ch = command
                elif command != "set":
                    show_err("Unknown command:" + command, win_help)
            else:
                command = cmd[0].strip()
                arg = cmd[1].strip()
                if command == "w" or command == "write":
                    folder = arg
                    ch = ord("w")
                elif command != "set":
                    show_err("Unknown command:" + command, win_help)
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
                show_err("No article was selected!! Select an article using s", win_help)
            else:
                if merge:
                    f = open(folder + '.html', "w")
                    print("<!DOCTYPE html>\n<html>\n<body>", file=f)
                elif not os.path.exists(folder):
                    os.makedirs(folder)
                num = 0
                for j,a in enumerate(articles): 
                    i = start + j
                    _id = a["id"]
                    if  _id not in sels:
                        continue
                    num += 1
                    paper_title = a['title']
                    show_info(paper_title + '...', win_help)
                    file_name = paper_title.replace(' ','_').lower()
                    if not merge:
                       f = open(folder + '/' + file_name + '.html', "w")
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
                show_msg(str(num)+ " articles were downloaded and saved into:" + folder, win_help)
            ch = get_key(std)
    return "" 

def get_cmd(opts, ranges, inds, win):
    cmd = minput(win, 0, 0, ":")
    # cmd = re.split(r'\s(?=")', cmd) 
    cmd = shlex.split(cmd)
    if len(cmd) == 0:
        return ['<Enter>']
    if len(cmd) == 1:
        return cmd
 
    command = cmd[0].strip()
    arg = cmd[1].strip()
    if command != "set":
        return cmd
    else:
        arg = arg.split('=')
        if len(arg) == 1:
            show_err("use 'set opt=val' to set an option, press any key ...", win)
        else:
            key = arg[0].strip()
            val = arg[1].strip()
            if key not in opts:
                show_err(key + " is an invalid option, press any key...", win)
            else:
               mi = list(opts.keys()).index(key)
               if key not in ranges:
                   opts[key] = val
               else:
                    if val in ranges[key]:
                        opts[key] = val
                        inds[key] = ranges[key].index(val)
                    else:
                        show_err(val + " is invalid for " + key + ", press any key ...", win)
        return cmd

def refresh_menu(opts, menu_win, sel):
    global clG
    clear_screen(menu_win)
    for k, v in opts.items():
       if k == sel:
           mprint("{:<15}:{}".format(k, v), menu_win, clG)
       else:
           mprint("{:<15}:{}".format(k, v), menu_win)

def get_sel(opts, mi):
    mi = max(mi, 0)
    mi = mi if mi < len(opts) else 0 
    return list(opts)[mi], mi

def show_info(msg, win, color=cC):
    clear_screen(win)
    print_there(0,1, msg, win, color)

def show_msg(msg, win, color=cG):
   show_info(msg, win, color)
   win.getch()
   clear_screen(win)

def show_err(msg, win, color=cR):
    show_msg(msg, win, color)

def show_menu(std, opts, ranges, inds):

    mi = 0
    ch = 'a'
    mode = 'm'

    rows, cols = std.getmaxyx()
    height = max(len(opts),rows-10)
    width = cols//2 - 10
    menu_win = cur.newwin(height, width, 3, 5)
    sub_menu_win = cur.newwin(height, width,5, width + 5)
    win_help = cur.newwin(1, cols, rows-1,0) 
    hide_cursor()
    _help = False
    while ch != ord('q'):
        clear_screen(std)
        clear_screen(sub_menu_win)
        sel,mi = get_sel(opts, mi)
        if sel in ranges:
            opts[sel] = ranges[sel][inds[sel]]

        refresh_menu(opts, menu_win, sel)
        if mode == 's':
           if sel not in ranges:
              opts[sel]=""
              refresh_menu(opts, menu_win, sel)
              val = minput(menu_win, mi + 0, 0, "{:<15}".format(sel) + ":") 
              opts[sel] = val
              mi += 1
              sel,mi = get_sel(opts, mi)
              refresh_menu(opts, menu_win, sel)
              mode = 'm'
           else:
              count = 0
              for vi, v in enumerate(ranges[sel]):
                count += 1
                if count > 10:
                    break
                if vi == inds[sel]:
                   mprint(str(v),sub_menu_win, cO)
                else:
                   mprint(str(v), sub_menu_win, cC)

        if _help:
            if mode == 'm':
                show_info("Press <Enter> to set a value, r to search and q to quit.", win_help)
            else:
                show_info("Press <Enter> to set a value", win_help)
        ch = get_key(std)
        
        if ch == ord(':'):
            cmd = get_cmd(opts, ranges, inds, win_help)
        if ch == ord("h"):
            _help = not _help
        if ch == cur.KEY_DOWN:
            if mode == "m":
                mi += 1
            elif sel in ranges:
                inds[sel] += 1
        if ch == cur.KEY_UP:
            if mode == "m":
                mi -= 1
            elif sel in ranges:
                inds[sel] -= 1

        if sel in ranges:
            inds[sel] = min(inds[sel], len(ranges[sel]))
            inds[sel] = max(inds[sel], 0)
        if  ch == cur.KEY_ENTER or ch == 10 or ch == 13:
            mode = 's' if mode == 'm' else 'm'
        if ch == cur.KEY_RIGHT:
            mode = 's'
        elif ch == cur.KEY_LEFT:
            mode = 'm'
        elif ch == ord('q'):
            # show_cursor()
            break;
        elif ch == ord('r') or ch == ord('g'): 
            return ch
    return ch

def main(std):

    filters = {}
    now = datetime.datetime.now()
    filter_items = ["year", "conference", "dataset", "task"]
    opts = load_obj("query_opts")
    if opts is None:
        opts = {"query":"reading comprehension", "year":"","page":1,"page-size":30,"task":"", "conference":"", "dataset":""}
    ranges = {
            "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
            "page":[str(y) for y in range(1,100)],
            "page-size":[str(y) for y in range(30,100,10)], 
            "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
            "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
            "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ]
            }
    inds = load_obj("query_inds")
    if inds is None:
        inds = { "conference":0, "year":0, "page":0, "page-size":0, "task":0, "dataset":0 }

    for opt in opts:
       if opt in ranges:
           opts[opt] = ranges[opt][inds[opt]]
    cur.start_color()
    cur.use_default_colors()
    for i in range(0, cur.COLORS):
        cur.init_pair(i + 1, i, -1)
    cur.init_pair(250, cur.COLOR_WHITE, cur.COLOR_BLUE)

    clear_screen(std)
    print_there(2,0, "<< Nodreader V 1.0 >>".center(80), std)
    ch = ord('a')
    while ch != ord('q'):
        ch = show_menu(std, opts, ranges, inds)
        save_obj(opts, "query_opts")
        save_obj(inds, "query_inds")
        if chr(ch) == 'r' or chr(ch) == 'g':
            for k,v in opts.items():
                if k in filter_items and v and v != "All":
                    filters[k] = str(v)
            clear_screen(std)
            try:
                ret = request(std, opts["query"], opts["page"], opts["page-size"], filters)
                if ret:
                    show_err(ret, std)
            except KeyboardInterrupt:
                ch = ord('q')
                show_cursor()

if __name__ == "__main__":
    wrapper(main)
