import requests
from bs4 import BeautifulSoup
import json
import string

# Step 1: Scrape top 500 tech names from tomba.io
url = "https://docs.tomba.io/data/technology/top-500-web-technologies-2026"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

tech_dict = {}
for row in soup.find_all("tr")[1:]:
    cols = row.find_all("td")
    if len(cols) == 3:
        name = cols[1].text.strip()
        tech_dict[name] = []

with open("HailMarry.json", "w", encoding="utf-8") as f:
    json.dump(tech_dict, f, indent=2)

print(f"Found {len(tech_dict)} technologies from tomba.io")

# Step 2: Fetch all Wappalyzer technology files
wappalyzer_data = {}
letters = list(string.ascii_lowercase)

for letter in letters:
    raw_url = f"https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies/{letter}.json"
    res = requests.get(raw_url)
    if res.status_code == 200:
        try:
            data = res.json()
            for tech_name, tech_info in data.items():
                wappalyzer_data[tech_name.lower()] = {
                    "_original_name": tech_name,
                    **tech_info
                }
        except Exception:
            pass
    print(f"Fetched: {letter}.json")

# Patterns that are too generic
BLOCKLIST = {
    "<div", "<div ", '<div class=', '<div class="', "<form", "<input",
    "<body", '<body class=', "<span", "<section", "<header", "<footer",
    "<script", "<link", "<meta", "<html", "<head", "<!doctype", "text/html",
    "server", "powered", "content", "assets", "/assets/", "index", "default",
    "static", "public",
    "python", "ruby", "java", "node", "perl", "scala", "golang", "swift",
    "kotlin", "rust"
}

def clean_pattern(p):
    """Strip Wappalyzer regex syntax, keep only plain string prefix."""
    if not isinstance(p, str):
        return ""
    split_chars = ["\\;", "\\d", "\\w", "\\s", "(", "["]
    for c in split_chars:
        p = p.split(c)[0]
    return p.lower().strip()

def is_quality(cleaned, require_special=False):
    """Return True if the cleaned pattern is specific enough."""
    if not cleaned or len(cleaned) < 6 or cleaned in BLOCKLIST or cleaned.startswith("<"):
        return False
    if require_special:
        has_special = any(c in cleaned for c in "./:-_")
        if not has_special:
            return False
    else:
        has_special = any(c in cleaned for c in "./:-_")
        if not has_special and len(cleaned) < 10:
            return False
    return True

def extract_fingerprints(tech_info):
    """Extract a wider set of fingerprints from a Wappalyzer tech entry."""
    fingerprints = set()

    def add(raw, require_special=False):
        if not isinstance(raw, str):
            return
        cleaned = clean_pattern(raw)
        if is_quality(cleaned, require_special=require_special):
            fingerprints.add(cleaned)

    # 1️⃣ Scripts — paths, lower bar
    for key in ("scriptSrc", "script"):
        val = tech_info.get(key, [])
        if isinstance(val, str):
            val = [val]
        for v in val:
            add(v)

    # 2️⃣ HTML — slightly looser
    val = tech_info.get("html", [])
    if isinstance(val, str):
        val = [val]
    for v in val:
        cleaned = clean_pattern(v)
        tech_keywords = ["wordpress", "shopify", "drupal", "magento", "joomla"]
        if not any(c in cleaned for c in "./:-_") and any(kw in cleaned for kw in tech_keywords):
            fingerprints.add(cleaned)
        else:
            add(v, require_special=True)

    # 3️⃣ URL paths
    val = tech_info.get("url", "")
    if isinstance(val, str):
        val = [val]
    for v in val:
        add(v)

    # 4️⃣ Headers
    for header_name, pattern in (tech_info.get("headers") or {}).items():
        if not isinstance(pattern, str):
            continue
        cleaned_value = clean_pattern(pattern)
        if cleaned_value and cleaned_value not in BLOCKLIST and len(cleaned_value) >= 3:
            fingerprints.add(f"{header_name.lower()}: {cleaned_value}")

    # 5️⃣ Meta tags
    for meta_name, pattern in (tech_info.get("meta") or {}).items():
        if isinstance(pattern, str):
            add(pattern, require_special=False)

    # 6️⃣ Cookies
    for cookie_name in (tech_info.get("cookies") or {}).keys():
        cleaned = cookie_name.lower().strip()
        if len(cleaned) >= 4 and cleaned not in BLOCKLIST:
            fingerprints.add(cleaned)

    # 7️⃣ CSS
    val = tech_info.get("css", [])
    if isinstance(val, str):
        val = [val]
    for v in val:
        add(v, require_special=True)

    # 8️⃣ Optional extra sources: images and link hrefs
    for key in ("img", "link"):
        val = tech_info.get(key, [])
        if isinstance(val, str):
            val = [val]
        for v in val:
            add(v)

    return list(fingerprints)

# Step 3: Match and extract fingerprints
for name in tech_dict:
    match = wappalyzer_data.get(name.lower())
    if match:
        tech_dict[name] = extract_fingerprints(match)

# Step 4: Drop techs with no fingerprints
before = len(tech_dict)
tech_dict = {k: v for k, v in tech_dict.items() if v}
dropped = before - len(tech_dict)
print(f"Dropped {dropped} technologies with no fingerprints")

# Step 5: Save Dictionary.json
with open("Dictionary.json", "w", encoding="utf-8") as f:
    json.dump(tech_dict, f, indent=2)

matched = len(tech_dict)
print(f"Done! {matched} technologies saved with fingerprints.")
