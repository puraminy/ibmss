#v2 tehran
import requests
import sys, os, getopt
import json
import getch as gh
from termcolor import colored
def switch(l, val):
    if not val in l:
       l.append(val)
    else: 
       l.remove(val)

def request(query, page = 0, merge=True, ls=False,  filters = None, sections = None):
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
    filters_str = json.dumps(filters)
    size = 15
    data = f'{{"query":"{query}","filters":{filters_str},"page":{page},"size":{20},"sort":null,"sessionInfo":""}}'
    print("data:", data)
    response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)

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
    if not merge and not os.path.exists(folder):
        os.makedirs(folder)

    articles = response.json()['searchResults']['results']
    if merge:
        f = open(folder + '.html', "w")
        print("<!DOCTYPE html>\n<html>\n<body>", file=f)
    ch = '0'
    sels = []
    full = []
    if ls:
        while ch != 'g':
            for i,a in enumerate(articles): 
                paper_title = a['title']
                item = str(i).rjust(2) +  ":" +  paper_title.ljust(40)[:80]               
                color = 'green'
                if str(i) in full:
                    color = 'blue'
                if str(i) in sels:
                   print(colored(item, color))
                else:
                   print(item)
            print("sels:", sels)
            inp = input("select:") #gh.getch()    
            inp = inp.split(' ')
            ch = inp[0]
            act = 'a'
            if len(inp) > 1:
                act = inp[1]
            if act == 'f':
                switch(full, ch)

            switch(sels, ch)
    for i,a in enumerate(articles): 
        paper_title = a['title']
        if sels and not str(i) in sels:
            continue
        print(i, ": ", a['title'])
        file_name = paper_title.replace(' ','_').lower()
        if not merge:
           f = open(folder + '/' + file_name + '.html', "w")
           print("<!DOCTYPE html>\n<html>\n<body>", file=f)
        print("<h1>" +  "New Paper" + "</h1>", file=f)
        print("<h1>" +  paper_title + "</h1>", file=f)
        for b in a['sections']:
            title =  b['title']
            if sections and  str(i) not in full  and title.lower() not in sections:
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
    print("Saved into:", folder)

def usage():
   print('request.py -q <query> -p <page> -y year')

def main(argv):
   query = ''
   merge = 'true'
   year = ''
   page = 0
   sects = 'abstract introduction conclusion'
   conf = ""
   dataset = ""
   task = ""
   ls = False
   try:
       opts, args = getopt.getopt(argv,"hlq:p:y:s:m:c:d:t:",["query=","page=","year=","sects=","merge=","conf=","dataset=","task="])
   except getopt.GetoptError:
      usage() 
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         usage()
         sys.exit()
      elif opt in ("-q", "--query"):
         query = arg
      elif opt in ("-p", "--page"):
         page = arg
      elif opt in ("-c", "--conf"):
         conf = arg
      elif opt in ("-d", "--dataset"):
         dataset = arg
      elif opt in ("-t", "--task"):
         task = arg
      elif opt in ("-y", "--year"):
         year = arg
      elif opt in ("-l", "--list"):
         ls = True
      elif opt in ("-m", "--merge"):
         sects = arg
      elif opt in ("-s", "--sects"):
         sects = arg
   print("query:", query)
   print("page:", page)
   print("year:", year)
   print("sects:", sects)
   print("merge:", merge)
   print("list:", ls)
   if not query:
     print('query is mandatory')
     sys.exit(2)
   
   filters = {}
   if conf != "":
      filters["conference"] =  conf
   if task != "":
      filters["task"] = task
   if dataset != "":
      filters["dataset"] =  dataset
   if year != "":
      filters["year"] =  year
   sect_list = []
   if sects != "all":
      sect_list = sects.split()
   request(query, page, merge =='true', ls, filters, sect_list)

if __name__ == "__main__":
   main(sys.argv[1:])
