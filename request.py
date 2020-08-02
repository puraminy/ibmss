#v2 tehran
import requests
import sys, os, getopt
import json

def request(query, page = 0, merge=True,  filters = None, sections = None):
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
    size = 20
    data = f'{{"query":"{query}","filters":{filters_str},"page":{page},"size":{20},"sort":null,"sessionInfo":""}}'
    print("data:", data)
    response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)

    year = ''
    if "year" in filters:
        year = filters['year']

    folder = query + '_' + str(year) + '_' + str(page)
    folder = folder.replace(' ','_')
    folder = folder.replace('__','_')
    if not merge and not os.path.exists(folder):
        os.makedirs(folder)

    articles = response.json()['searchResults']['results']
    if merge:
        f = open(folder + '.html', "w")
        print("<!DOCTYPE html>\n<html>\n<body>", file=f)

    for a in articles: 
        paper_title = a['title']
        file_name = paper_title.replace(' ','_').lower()
        print("getting ... ", a['title'])
        if not merge:
           f = open(folder + '/' + file_name + '.html', "w")
           print("<!DOCTYPE html>\n<html>\n<body>", file=f)
        print("<h1>" +  "New Paper" + "</h1>", file=f)
        print("<h1>" +  paper_title + "</h1>", file=f)
        for b in a['sections']:
            title =  b['title']
            if sections and title.lower() not in sections:
                print("ignoring " + title + " ")
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
    if merge:
        f.close()

def usage():
   print('request.py -q <query> -p <page> -y year')

def main(argv):
   query = ''
   merge = 'true'
   year = '0000'
   page = 0
   sects = 'all'
   try:
       opts, args = getopt.getopt(argv,"hq:p:y:s:m:",["query=","page=","year=","sects=","merge="])
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
      elif opt in ("-y", "--year"):
         year = arg
      elif opt in ("-m", "--merge"):
         sects = arg
      elif opt in ("-s", "--sects"):
         sects = arg
   print("query:", query)
   print("page:", page)
   print("year:", year)
   print("sects:", sects)
   print("merge:", merge)
   if not query:
     print('query is mandatory')
     sys.exit(2)
   
   filters = {}
   if year != "0000":
      filters["year"] =  year
   sect_list = []
   if sects != "all":
      sect_list = sects.split()
   request(query, page, merge =='true', filters, sect_list)

if __name__ == "__main__":
   main(sys.argv[1:])
