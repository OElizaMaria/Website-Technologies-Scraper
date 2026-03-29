import requests
import json
import string
import re
from bs4 import BeautifulSoup

WAPP_BASE_URL = "https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies/{}.json"

tech_dict = {}

# 
remove_generic = { "<div", "<div ", '<div class=', '<div class="',"<form", "<input", "<body", '<body class=',
    "<span", "<section", "<header", "<footer","<script", "<link", "<meta", "<html", "<head",
    "<!doctype", "text/html","server", "powered", "content", "assets", "/assets/","index", "default", "static", "public",
    "python", "ruby", "java", "node", "perl", "scala","golang", "swift", "kotlin", "rust"} 


# we clean the string to make it quicker to match in the scraper
    # technically cleaning is not necesarry but when building dictionary without it
    # the matching took too long to be suitable
def clean_string(n):

    if not isinstance(n, str):
        return []
    
    p = n.replace('^','').replace('$','').replace('\\/','/')
    p = re.sub(r'[\(\)]','',p)
    parts = p.split('|')
    res = []

    for part in parts:
        clean = part.split('\\;')[0].split('(')[0].split('[')[0].split('.*')[0]
        clean = clean.replace('\\.', '.').lower().strip()

        if clean:
            res.append(clean)
    return res

# check if its good pattern
def is_good(clean, source):
    
    #garbage check
    if not clean or clean in remove_generic:
        return False
    
    # they must have a certain length so its enough for a match
    if source in ['cookies','headers', 'meta']:
        return len(clean) >= 3
    
    if source in ['html','script','css']:
        if any(c in clean for c in "./_-"):
            return len(clean) >= 4
        return len(clean) >= 4
    return len(clean) >= 3

def extract_fingerprints(tech_info):
    fingerprints = set()
    mapping = {'js' : 'script', 'scriptSrc' : 'script',
                 'html': 'html','css': 'css','url': 'html',
                 'meta': 'meta','headers': 'headers','cookies': 'cookies'}
    
    for w_key, source_type in mapping.items():
        data = tech_info.get(w_key)
        if not data:
            continue

        i = []
        # checks what type it is
        if isinstance(data,str):
            i = [data]
        elif isinstance(data,list):
            i = data
        elif isinstance(data,dict):
            for k,v in data.items():
                i.append(k)
                if isinstance(v, str):
                    i.append(v)
        # cleans it and adds it
        for raw in i:
            potential = clean_string(raw)
            for s in potential:
                if is_good(s, source_type):
                    if source_type == 'headers' and ':' not in s:
                        fingerprints.add(s)
                    else:
                        fingerprints.add(s)
    return list(fingerprints)

try:
    # scrape top 500 technologies
    resp = requests.get("https://docs.tomba.io/data/technology/top-500-web-technologies-2026",timeout=15)
    soup = BeautifulSoup(resp.text,"html.parser")

    target_names = set()
    for i in soup.find_all("tr")[1:]:
        j = i.find_all("td")
        if len(j) >= 2:
            target_names.add(j[1].text.strip().lower())
except Exception as e:
    print("error")
    target_names = set()

wappalyzer_db = {}
# get the wappalyzer library
for char in string.ascii_lowercase + "0": 
    res = requests.get(WAPP_BASE_URL.format(char))
    if res.status_code == 200:
        wappalyzer_db.update(res.json())
final_dict = {}

hail_mary_list = []

#create the dictionaries
for name, info in wappalyzer_db.items():
    lower_name = name.lower()
    if lower_name in target_names:
        hail_mary_list.append(name)
        prints = extract_fingerprints(info)
        if prints:
            final_dict[name] = prints

with open("Dictionary.json", "w", encoding="utf-8") as f:
    json.dump(final_dict, f, indent=2)

with open("HailMary.json", "w", encoding="utf-8") as f:
    json.dump(hail_mary_list, f, indent=2)

print(f"Dictionary.json: {len(final_dict)} technologies")
print(f"HailMary.json: {len(hail_mary_list)} technologies")