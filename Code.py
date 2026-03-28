import pandas as pd
import aiohttp
import asyncio
import ssl
import json
import re
from bs4 import BeautifulSoup
from bs4 import Comment

# ssl context for bad certificates so request doesnt fail
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# loading dictionary which we match against
with open("Dictionary.json", "r", encoding="utf-8") as f:
    TECH = json.load(f)

#loading hail mary 
with open("HailMary.json", "r", encoding="utf-8") as f:
    wappalyzer_names = json.load(f)

#make req look legit
hdr = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


async def get(name, s):
    #we try a bunch of urls to make sure we get the website and we dont get false "not found" case
    urls = [f"https://{name}", f"https://www.{name}", f"http://{name}", f"http://www.{name}"]
    for url in urls:
        try:
            async with s.get(url, headers=hdr, timeout=aiohttp.ClientTimeout(total=20), ssl=ssl_context) as response:
                if response.status < 500: # even if its 404 for example, we can still scrape info (500 is server error)
                   
                   # get raw bytes and convert
                    raw = await response.read()
                    html = raw.decode(response.charset or "latin-1" ,errors="replace")
                    headers = dict(response.headers)
                    return html, headers
                
        except Exception:
            continue
    return None, {}


def get_info(html, resp_headers):
    soup = BeautifulSoup(html, "lxml")
    #info contains only needed info for match
    info = {"html":html, "scripts": [], "links":[], "meta":[], "headers": resp_headers, "cookies": {}}

    for s in soup.find_all("script", src=True):
        info["scripts"].append(s["src"])

    for l in soup.find_all("link", href=True):
        info["links"].append(l["href"])

    for m in soup.find_all("meta"):
        if m.get("name") == "generator":
            info["meta"].append(m.get("content", ""))

    set_cookie = resp_headers.get("Set-Cookie", "")
    for i in set_cookie.split(";"):
        i = i.strip()
        if "=" in i:
            key, val = i.split("=", 1)
            info["cookies"][key.strip().lower()] = val.strip().lower()

    return info

# match function for detection
def match(pattern, text):
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return pattern.lower() in text.lower()

# regex matching with our dictionary
def detect_tech(info):
    detected = []

    for tech, patterns in TECH.items():
        found = False

        for pattern in patterns:
            if found:
                break

            # we look for a match each time, if we found it we break to not cause overhead

            if ": " in pattern and not pattern.startswith("/"):
                header_name, header_pattern = pattern.split(": ", 1)
                header_val = info["headers"].get(header_name.lower(),"")
                if header_val and match(header_pattern, header_val):
                    found = True
                    break


            for cookie_name, cookie_val in info["cookies"].items():
                if match(pattern, cookie_name) or match(pattern, cookie_val):
                    found = True
                    break
            if found:
                break

            for src in info["scripts"]:
                if match(pattern, src):
                    found = True
                    break
            if found:
                break

            for href in info["links"]:
                if match(pattern, href):
                    found = True
                    break
            if found:
                break

            for meta in info["meta"]:
                if match(pattern, meta):
                    found = True
                    break
            if found:
                break

            if match(pattern, info["html"]):
                found = True
        if found:
            detected.append(tech)
        
        # last attemp(Hail Marry)
        # if we didnt find anything we just try to match the name
        # to anything EXCEPT the content
        if not detected:   
            soup = BeautifulSoup(info["html"], "lxml")
            inline_scripts = [s.get_text() for s in soup.find_all("script") if not s.get("src")]
            comments = [c for c in soup.find_all(string=lambda text: isinstance(text, Comment))]
            titles = [t.get_text() for t in soup.find_all("title")]
            headers = [h.get_text() for h in soup.find_all("h1")]
            list = info["scripts"] + info["links"]  + info["meta"] + inline_scripts + comments + titles + headers

            for name in wappalyzer_names:
                n = name.lower()
                if any(n in i.lower() for i in list):
                    detected.append(f"{name} (Hail Marry)")

    return detected


async def process_domain(idx, domain, session, semaphore):
    # the code is multithreaded because of the large dataset to look through
    async with semaphore:
        html, headers = await get(domain, session)
        if html is None:
            print(f"[{idx}] not found {domain}")
            return idx, domain, []
        info = get_info(html, headers) # extract necesarry info
        tech = detect_tech(info) #
    return idx, domain, tech


async def main():
    filename = "./input"
    df = pd.read_parquet(filename)

    # we limit to 50 threads
    semaphore = asyncio.Semaphore(50)
    connector = aiohttp.TCPConnector(limit=50, ssl=ssl_context)

    # we open sesson, give the tasks and wait for resp
    async with aiohttp.ClientSession(connector=connector) as s:
        tasks = [
            process_domain(idx, i, s, semaphore)
            for idx, i in enumerate(df["root_domain"])
        ]
        rasp = await asyncio.gather(*tasks, return_exceptions=True)

    distinct_techs = set()
    results = {}

    for result in rasp:
        if isinstance(result, Exception):
            continue
        idx, domain, techs = result
        results[domain] = techs
        for t in techs:
            distinct_techs.add(t)

    print(f"Total gasite {len(distinct_techs)}")

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return rasp


asyncio.run(main())