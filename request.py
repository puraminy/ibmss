#change
import requests
import sys, os, getopt
import json

def request(query, page = 0, filters = None):
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
    data = f'{{"query":"{query}","filters":{{"year":2020}},"page":{page},"size":10,"sort":null,"sessionInfo":""}}'
    source = "ACL"
    page =1
    data = '{"query":"reading comprehension","filters":{},"page":0,"size":10,"sort":null,"sessionInfo":""}'
    #data = f'{{"query":"{query}","filters":{{"year":"{year}"}},"page":{page},"size":10,"sort":null,"sessionInfo":""}}'
    filters = {'year':"2020"}
    filters_str = json.dumps(filters)
    #data = f'{{"query":"{query}","filters":{{{filters_str} }},"page":{page},"size":10,"sort":null,"sessionInfo":""}}'
    print("data:", data)
    response = requests.post('https://dimsum.eu-gb.containers.appdomain.cloud/api/scholar/search', headers=headers, data=data)
    folder = query + ' ' + str(year) + str(page)
    if not os.path.exists(folder):
        os.makedirs(folder)

    articles = response.json()['searchResults']['results']
    for a in articles: 
        paper_title = a['title']
        print("getting ... ", a['title'])
        f = open(folder + '/' + a['title'] + '.vvc', "w")
        print(paper_title, file=f)
        for b in a['sections']:
            title =  b['title']
            print("", file=f)
            print(title, file=f)
            print("", file=f)
            for c in b['fragments']:
                    text= c['text']
                    f.write(text)
        f.close()


def main(argv):
   query = ''
   merge_all = False
   sections = 'all' 
   page = 0
   try:
      opts, args = getopt.getopt(argv,"hq:p:",["query=","page="])
   except getopt.GetoptError:
      print('request.py -q <query> -p <page>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('request.py -q <query> -p <page>')
         sys.exit()
      elif opt in ("-q", "--query"):
         query = arg
      elif opt in ("-p", "--page"):
         page = arg
   print("query:", query)
   print("page:", page)
   if not query:
     print('query is mandatory')
     sys.exit(2)
   request(query, page)

if __name__ == "__main__":
   main(sys.argv[1:])
