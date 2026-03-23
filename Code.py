import pandas as pd
import requests
import aiohttp
import asyncio


async def get(name, s):

    urls = [f"https://{name}", f"https://{name}/", f"http://{name}",f"http://{name}/", f"{name}", f"https://www.{name}",
            f"https://www.{name}/",f"http://www.{name}", f"http://www.{name}/",f"www.{name}", f"www.{name}/"]
    for url in urls:
        try:
            async with s.get(url, timeout= aiohttp.ClientTimeout(total = 10), ssl = False) as response:
                print(f"  {url} -> status {response.status}") 
                if response.status == 200:
                    raw = await response.read()
                    encoding = response.charset or "utf-8"
                    return raw.decode(encoding, errors = "replace")
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            continue
    return -1


async def main():
    filename = "./input"
    df = pd.read_parquet(filename)

    async with aiohttp.ClientSession() as s:
        for idx, i in enumerate(df["root_domain"]): #luam coloana de sub root domain
            rasp = await get(i, s)
            if rasp == -1:
                print(f"not found {idx} {i}")
    
        
asyncio.run(main())
            