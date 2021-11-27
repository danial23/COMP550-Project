# Nov. 25th 2021
# Molly Jacobsen

# Sample script using wikimedia API to extract data into CSV files

import requests

S = requests.Session()

URL = "https://mediawiki.org/w/api.php"

PARAMS = {
    "action": "query",
    "prop": "revisions",
    "titles": "Main Page",
    "rvlimit": "100",
    "rvprop": "timestamp|user|comment|context|tags",
    "rvdir": "newer",
    "rvslots": "main",
    "formatversion": "2",
    "format": "json"
}

R = S.get(url=URL, params=PARAMS)
DATA = R.json()

PAGES = DATA["query"]["pages"]

for page in PAGES:
    print(page["revisions"])