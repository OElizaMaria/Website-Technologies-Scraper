import requests
import json
import string
import re
from bs4 import BeautifulSoup


# we get the top 500 most used technologies
response = requests.get("https://docs.tomba.io/data/technology/top-500-web-technologies-2026")
soup = BeautifulSoup(response.text, "html.parser")
tech_dict = {}

for i in soup.find_all("tr")[1:]:
    j = i.find_all("td")
    if len(j) == 3:
        n = j[1].text.strip()
        tech_dict[n] = []

with open("HailMary.json", "w", encoding="utf-8") as i:
    json.dump(tech_dict, i, indent=2)

tech_data = {}
# they are ordered alphabetically
letters = list(string.ascii_lowercase)

for i in letters:
    url = f"https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies/{i}.json"
    res = requests.get(url)
    if res.status_code == 200:
        try:
            data = res.json()
            for tech_name, tech_info in data.items():
                tech_data[tech_name.lower()] = tech_info
        except Exception:
            pass

remove_generic = { "<div", "<div ", '<div class=', '<div class="',"<form", "<input", "<body", '<body class=',
    "<span", "<section", "<header", "<footer","<script", "<link", "<meta", "<html", "<head",
    "<!doctype", "text/html","server", "powered", "content", "assets", "/assets/","index", "default", "static", "public",
    "python", "ruby", "java", "node", "perl", "scala","golang", "swift", "kotlin", "rust"} 

def cleanup(p):
    # remove regex

    if not isinstance(p, str):
        return ""
    
    # cuts unecesary stuff like  wp-content\\;version
    split_chars = ["\\;","\\d","\\w","\\s","(","["]
    for c in split_chars:
        p = p.split(c)[0]
    # replace all unecesary characters for easier match
    p = re.sub(r"\\[dwbs]", "", p)
    p = re.sub(r"\(.*?\)|\[.*?\]", "", p)
    p = re.sub(r"\.\*|\.\+", "", p)
    p = re.sub(r"\^|\$", "", p)

    # unescape characters
    p = p.replace(r"\.", ".").replace(r"\/", "/")

    return p.lower().strip()