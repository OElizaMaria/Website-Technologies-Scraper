import pandas as pd
import requests
import aiohttp
import asyncio
import ssl
from bs4 import BeautifulSoup

#de revenit aici
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# de rectificat aici
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

    urls = [  f"https://{name}", f"https://www.{name}", f"http://{name}", f"http://www.{name}"]
    for url in urls:
        try:
            async with s.get(url, headers = hdr, timeout= aiohttp.ClientTimeout(total = 10), ssl=ssl_context) as response:
                #print(f"  {url} -> status {response.status}") 
                if response.status < 500:
                    raw = await response.read()
                    encoding = response.charset or "utf-8"
                    return raw.decode(encoding, errors = "replace")
        except Exception as e:
            #print(url, "ERROR:", repr(e))
            continue
    return -1

def get_info(html):
    soup = BeautifulSoup(html,"lxml")
    info = {"scripts":[], "links":[], "meta":[],"html":html.lower()}

    for s in soup.find_all("script", src = True):
        info["scripts"].append(s["src"].lower())

    for l in soup.find_all("link", href= True):
        info["links"].append(l["href"].lower())

    for m in soup.find_all("meta"):
        if m.get("name") == "generator":
            info["meta"].append(m.get("content","").lower())
    return info

def detect_tech(info):
    
    detected = []

    combined = (info["html" + " ".join(info["scripts"])+ " ".join(info["links"])+ " ".join(info["meta"])])

    for tech, fingerprints in TECH.items():
        for f in fingerprints:
            if f in combined:
                detected.append(tech)
                break
    return detected

async def main():
    filename = "./input"
    df = pd.read_parquet(filename)
    c = aiohttp.CookieJar()


    async with aiohttp.ClientSession(cookie_jar = c) as s:
        for idx, i in enumerate(df["root_domain"]): #luam coloana de sub root domain
            rasp = await get(i, s)
            if rasp == -1:
                print(f"not found {idx} {i}")
    
        
asyncio.run(main())
            