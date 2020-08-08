#v2 tehran
import requests
import sys, os 
import datetime
import shlex
# import re
import textwrap
import json
from termcolor import colored
import getch as gh
from utility import *



def err(msg):
    print("")
    print("\t"+msg)
    ch = get_key()
    return ch
def switch(d, art, ch):
    key = art["id"]
    sects = 'abstract introduction conclusion'
    if not key in d:
        if ch == 's':
           d[key] = sects.split(' ')
        else:
           d[key] = [s["title"].lower() for s in art["sections"]]
    else: 
        del d[key]

def request(query, page = 1, size=40, filters = None):
    page -= 1
    if not query:
        return "query is mandatory!"
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
    print("\n\n\n\t\tGetting articles...")
    try:
        response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)

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
    cend = '\x1b[0m'
    cend2 = '\033[0m'
    cgray = '\033[90m'
    if N == 0:
        return "No result fond"
    while ch != 'q' and ch != 'g':
        os.system('clear')
        art = articles[k]
        art_id = art['id']
        if mode == 'd':
           a = art
           os.system('clear')
           print("")
           sn = 0
           sects_num = len(a["sections"])
           title = "\n".join(textwrap.wrap(a["title"], 80)) # wrap at 60 characters
           top =  "\t["+str(k)+"] " + title
           print(textwrap.indent(colored(top,'yellow'), " "*10)) # indent with 10 spaces    
           for b in a["sections"]:
               if sn != sc:
                   if art_id in sels and b["title"].lower() in sels[art_id]:
                       print('\x1b[0;30;44m' + b["title"] + cend)
                   else:
                       print('\x1b[1;30;38m' + b["title"] + cend)
                   # print(cgray + b["title"] + cend2)
               else:
                   frags_num = len(b['fragments'])
                   sect_title = b["title"] + f"({fc+1}/{frags_num})" 
                   #print(colored(sect_title + , 'yellow'))
                   if art_id in sels and b["title"].lower() in sels[art_id]:
                       print('\x1b[0;30;44m' + sect_title + cend)
                   else:
                       print('\x1b[1;30;38m' + sect_title + cend)
                   fn = 0
                   for c in b['fragments']:
                       if fn == fc:
                          text= c['text']
                          frag = "\n".join(textwrap.wrap(text, 80)) # wrap at 60 characters
                          print(textwrap.indent(colored(frag ,'green'), " "*10)) # indent with 10 spaces                          
                       fn += 1
               sn += 1
        else:
            print("\n\n")
            for j,a in enumerate(articles[start:start + 15]): 
                i = start + j
                paper_title =  a['title']
                dots = ""
                if len(paper_title) > 80:
                   dots = "..."
                item = "{:>5}{:4}{}".format(i, ":", paper_title[:80] + dots)               
                color = 'white'
                if a["id"] in sels:
                    color = 'green'
                if i == k:
                    color = 'yellow'

                print(colored(item, color))

        #print(":", end="", flush=True)
        ch = get_key()

        if ch == 'f' or ch == 's':
            switch(sels, art, ch)

        if ch == 'a':
            for ss in range(start,start+15):
                  rr = articles[ss]
                  switch(sels, rr, 's')

        if ch == 'c' and mode == 'd':
            cur_sect = art["sections"][sc]["title"].lower()
            if art_id in sels:
                if cur_sect in sels[art_id]:
                    sels[art_id].remove(cur_sect)
                else:
                    sels[art_id].append(cur_sect)
            else:
                sels[art_id] = [cur_sect]
        if ch == 'p':
            k-=1

        if ch == 'n':
            k+=1
        if ch == "right" and mode == 'd': 
                fc += 1
        if ch == 'l' or (len(ch) == 1 and ord(ch) == 127):
            mode = 'list'
        if ch == 'd' or ch == 'right' or (len(ch) == 1 and  (ord(ch) == 10 or ord(ch) == 9)):
            if mode == 'list':
                mode = 'd'
                fc = 0
                sc = -1
        elif ch == 'left':
            if mode == 'd':
                fc -= 1
        elif ch == 'up':
            if mode == 'd': 
                sc -= 1
                fc = 0
            else:
                k -=1
        elif ch == 'down':
            if mode == 'd':
                sc += 1
                fc = 0
            else:
                k +=1
        elif ch == "home":
            if mode == 'd':
                sc = -1
                fc = 0
            else:
                k = start
        elif ch == "end":
            if mode == 'd':
                sc = sects_num
                fc = 0
            else:
                k = start + 14

        if mode == 'd':
            if fc < 0:
                fc = 0
                if sc >= 0:
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
        sc = max(sc, -1)
        k = max(k, 0)
        k = min(k, size-1)
        if k >= start + 15:
            ch = 'pgdown'
        if k < start:
            ch = "prev_pg"
        if ch == 'pgdown':
            start += 15
            start = min(start, N - 15)
            k = start
        if ch == 'pgup' or ch == 'prev_pg':
            start -= 15
            start = max(start, 0)
            k = start + 14 if ch == 'prev_pg' else start
        if ch == 'w' or ch == 'm':
            merge = ch == 'm'
            if not sels:
                print_there(80,10,colored("No article selected!!",'red'))
            else:
                os.system("clear")
                if merge:
                    f = open(folder + '.html', "w")
                    print("<!DOCTYPE html>\n<html>\n<body>", file=f)
                elif not os.path.exists(folder):
                    os.makedirs(folder)
                for j,a in enumerate(articles): 
                    i = start + j
                    paper_title = a['title']
                    print(i, ",")
                    file_name = paper_title.replace(' ','_').lower()
                    if not merge:
                       f = open(folder + '/' + file_name + '.html', "w")
                       print("<!DOCTYPE html>\n<html>\n<body>", file=f)
                    print("<h1>" +  "New Paper" + "</h1>", file=f)
                    print("<h1>" +  paper_title + "</h1>", file=f)
                    _id = a["id"]
                    for b in a['sections']:
                        title =  b['title']
                        if sels and _id in sels:
                            _sect = sels[_id]
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
                print(" were downloaded and saved into:" + folder)
            ch = get_key()
    return "" 


filters = {}
now = datetime.datetime.now()
filter_items = ["year", "conference", "dataset", "task"]
opts = {"query":"reading comprehension", "year":"","page":1,"page-size":30,"task":"", "conference":"", "dataset":""}
ranges = {
        "year":["All"] + [str(y) for y in range(now.year,2010,-1)], 
        "page":range(1,1000),
        "page-size":range(30,100,10), 
        "task": ["All", "Reading Comprehension", "Machine Reading Comprehension","Sentiment Analysis", "Question Answering", "Transfer Learning","Natural Language Inference", "Computer Vision", "Machine Translation", "Text Classification", "Decision Making"],
        "conference": ["All", "Arxiv", "ACL", "Workshops", "EMNLP", "IJCNLP", "NAACL", "LERC", "CL", "COLING", "BEA"],
        "dataset": ["All","SQuAD", "RACE", "Social Media", "TriviaQA", "SNLI", "GLUE", "Image Net", "MS Marco", "TREC", "News QA" ]
        }
ind = { "conference":0, "year":0, "page":0, "page-size":0, "task":0, "dataset":0 }

mi = 0
ci = 0
confs = ["", "ACL","CLING","MSI","CLI"]
if __name__ == "__main__":
   ch = 'a'
#   while ch != 't':
#       ch = get_key()
#       print(ch)
#       print(ord(ch))
#       print(ord(ch).encode())
#       print(ord(ch).encode() == 27)
#
   mode = 'm'
   hide_cursor()
   _help = False
   for opt in opts:
      if opt in ranges:
          opts[opt] = ranges[opt][ind[opt]]
   while ch != 'q':
       os.system('clear')
       print("\n")
       print("<< Nodreader V 1.0 >>".center(80))
       print("\n")
       sel = list(opts)[mi]
       if sel in ranges:
           opts[sel] = ranges[sel][ind[sel]]
       for k, v in opts.items():
          if k == sel:
              if mode == 'm' or sel in ranges:
                  print(colored("\t{:<15}:{}".format(k, v),"yellow"))
              if mode == 's':
                if sel not in ranges:
                    val = input(colored("\t{:<15}:".format(k),"yellow"))
                    opts[sel] = val
                    mode = 'm'
                else:
                    count = 0
                    for vi, v in enumerate(ranges[sel]):
                      count += 1
                      if count > 10:
                          break
                      if vi == ind[sel]:
                         print(colored("\t\t\t" + str(v), 'green'))
                      else:
                         print(colored("\t\t\t" + str(v), 'blue'))
          else:
              print("\t{:<15}:{}".format(k, v))
       if _help:
           if mode == 'm':
               print("\n\nPress right arrow key to enter or a select a value, Press g to run the query")
           else:
               print("\n\nAfter selcting a value, press left arrow key to return to main menu")
       ch = get_key()

       if ch == "h":
           _help = not _help
       if ch == "down":
           if mode == "m":
               mi += 1
           elif sel in ranges:
               ind[sel] += 1
       if ch == "up":
           if mode == "m":
               mi -= 1
           elif sel in ranges:
               ind[sel] -= 1

       mi = max(mi, 0)
       mi = mi if mi < len(opts) else 0 
       if sel in ranges:
           ind[sel] = min(ind[sel], len(ranges[sel]))
           ind[sel] = max(ind[sel], 0)
       if (len(ch) == 1 and  (ord(ch) == 10 or ord(ch) == 9)):
           mode = 's' if mode == 'm' else 'm'
       if ch == "right": 
           mode = 's'
       elif ch == "left":
           mode = 'm'
       elif ch == 'q':
           show_cursor()
           break;
       elif ch == 'r' or ch == 'g' or (sel == "Go!" and len(ch) ==1 and ord(ch) == 10):
           print("")
           for k,v in opts.items():
               if k in filter_items and v and v != "All":
                   print(k,v)
                   filters[k] = str(v)
           os.system('clear')
           try:
               ret = request(opts["query"], opts["page"], opts["page-size"], filters)
               if ret:
                   err(ret)
           except KeyboardInterrupt:
               show_cursor()
               ch = 'q'


   print("")
