# Nov. 25th 2021
# Molly Jacobsen

# Sample script using wikimedia API to extract data into CSV files

import requests
import json
import time

S = requests.Session()
S.headers.update({"User-Agent" : "script (danialmtmdmhr23@gmail.com)", "Accept-encoding" : "gzip"})
API = "https://en.wikipedia.org/w/api.php"


def dump_data(data):
    pass


def get_all_revisions(title):
    start_time = time.time() #####

    PARAMS = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "flags|timestamp|userid|size|comment|tags",
        "rvslots": "main",
        "rvlimit": "max",
        "formatversion": "2",
        "format": "json",
        "maxlag" : "2",
    }

    R = S.get(url=API, params=PARAMS)
    DATA = R.json()

    if "error" in DATA or "warning" in DATA:
        print(json.dumps(DATA, indent=4))
        return None
    
    PAGE = DATA["query"]["pages"][0]
    revisions = PAGE["revisions"]

    while "continue" in DATA:

        PARAMS.update({"rvcontinue" : DATA["continue"]["rvcontinue"]})
        
        R = S.get(url=API, params=PARAMS)
        DATA = R.json()

        if "error" in DATA or "warning" in DATA:
            print(json.dumps(DATA, indent=4))
            return None
        
        PAGE = DATA["query"]["pages"][0]
        revisions += PAGE["revisions"]
    
    end_time = time.time() #####

    print(end_time - start_time) ####

    return revisions


def main():
    revisions = get_all_revisions("SQLite")
    print(revisions)
    print(len(revisions))


if __name__ == "__main__":
    main()