import requests
from bs4 import BeautifulSoup
import json
import string
import re

# --- CONFIGURATION ---
TOMBA_URL = "https://docs.tomba.io/data/technology/top-500-web-technologies-2026"
WAPP_BASE_URL = "https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies/{}.json"

# Patterns that appear in almost every website and provide zero signal
BLOCKLIST = {
    "<div", "<form", "<input", "<body", "<span", "<section", "<header", "<footer",
    "<script", "<link", "<meta", "<html", "<head", "<!doctype", "text/html",
    "server", "powered", "content", "assets", "/assets/", "index", "default",
    "static", "public", "jquery", "google", "cloudflare", "utf-8"
}

def clean_regex_to_strings(raw_regex):
 
    if not isinstance(raw_regex, str):
        return []

    # 1. Remove common regex noise that doesn't help string matching
    # Remove anchors, non-capturing groups, and escape slashes
    p = raw_regex.replace('^', '').replace('$', '').replace('\\/', '/')
    
    # 2. Handle the "OR" logic (the pipe symbol)
    # Wappalyzer loves (v1|v2|v3). We want all of them.
    # We strip parentheses and split by pipe
    p = re.sub(r'[\(\)]', '', p)
    parts = p.split('|')

    results = []
    for part in parts:
        # Strip trailing regex logic like version captures (;version:\\d)
        # or greedy matches (.*)
        clean = part.split('\\;')[0].split('(')[0].split('[')[0].split('.*')[0]
        clean = clean.replace('\\.', '.').lower().strip()
        
        if clean:
            results.append(clean)
    return results

def is_quality(cleaned, source_type):
    """
    Determine if a string is a good 'fingerprint' based on where it came from.
    """
    if not cleaned or cleaned in BLOCKLIST:
        return False
    
    # Logic for Cookies/Headers: High signal, can be shorter
    if source_type in ['cookies', 'headers']:
        return len(cleaned) >= 3
    
    # Logic for HTML/Scripts: Needs to be more unique
    if source_type in ['html', 'scripts', 'css']:
        # If it's a path (contains / or .) it's usually high quality
        if any(c in cleaned for c in "./_-"):
            return len(cleaned) >= 5
        return len(cleaned) >= 8 # Plain words must be long to avoid false positives
    
    return len(cleaned) >= 5

def extract_fingerprints(tech_info):
    """Extracts a high-coverage set of fingerprints from Wappalyzer JSON."""
    fingerprints = set()

    # Define mapping of Wappalyzer keys to our internal source types
    mapping = {
        'js': 'scripts',
        'scriptSrc': 'scripts',
        'html': 'html',
        'css': 'css',
        'url': 'html',
        'meta': 'meta',
        'headers': 'headers',
        'cookies': 'cookies'
    }

    for wapp_key, source_type in mapping.items():
        data = tech_info.get(wapp_key)
        if not data:
            continue

        # Wappalyzer data can be a string, a list, or a dict (for headers/meta/cookies)
        items_to_process = []
        if isinstance(data, str):
            items_to_process = [data]
        elif isinstance(data, list):
            items_to_process = data
        elif isinstance(data, dict):
            # For dicts, we care about both the Key and the Value (regex)
            for k, v in data.items():
                items_to_process.append(k)
                if isinstance(v, str):
                    items_to_process.append(v)

        for raw in items_to_process:
            potential_strings = clean_regex_to_strings(raw)
            for s in potential_strings:
                if is_quality(s, source_type):
                    # For headers, we keep the "key: val" format for your scraper
                    if source_type == 'headers' and ":" not in s:
                        # We don't force formatting here because we processed keys/vals separately
                        fingerprints.add(s)
                    else:
                        fingerprints.add(s)

    return list(fingerprints)

# --- EXECUTION ---

# 1. Scrape Top 500 Names
print(f"Scraping technology list from {TOMBA_URL}...")
try:
    resp = requests.get(TOMBA_URL, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Using a set for names to ensure uniqueness
    target_names = set()
    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            target_names.add(cols[1].text.strip().lower())
    print(f"Targeting {len(target_names)} technologies.")
except Exception as e:
    print(f"Error scraping Tomba: {e}")
    target_names = set()

# 2. Fetch Wappalyzer Data
wappalyzer_db = {}
for char in string.ascii_lowercase + "0": # Wappalyzer also has a _ (0) file
    print(f"Fetching {char}.json...", end="\r")
    res = requests.get(WAPP_BASE_URL.format(char))
    if res.status_code == 200:
        wappalyzer_db.update(res.json())

# 3. Match and Build
final_dict = {}
hail_mary_list = []
for name, info in wappalyzer_db.items():
    lower_name = name.lower()
    
    # Check if this technology is one of the Top 500 from Tomba
    if lower_name in target_names:
        # 1. Add to Hail Mary (The name-only backup)
        hail_mary_list.append(name)
        
        # 2. Extract deep fingerprints for the main Dictionary
        prints = extract_fingerprints(info)
        if prints:
            final_dict[name] = prints

# 4. Save Files
with open("Dictionary.json", "w", encoding="utf-8") as f:
    json.dump(final_dict, f, indent=2)

with open("HailMary.json", "w", encoding="utf-8") as f:
    json.dump(hail_mary_list, f, indent=2)

print(f"\nSuccess!")
print(f"Dictionary.json: {len(final_dict)} techs with active fingerprints.")
print(f"HailMary.json: {len(hail_mary_list)} tech names for backup matching.")