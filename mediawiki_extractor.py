# Nov. 25th 2021
# Molly Jacobsen
# Danial Motamedi Mehr
# Tigran Ionnisian

# Data collection script

import requests
import json
import time
import os
import functools
import logging
import sys


_S = requests.Session()
_S.headers.update({"User-Agent": "script (danialmtmdmhr23@gmail.com)", "Accept-encoding": "gzip"})
_API = "https://en.wikipedia.org/w/api.php"
_DATASET_DIR = "dataset"
_titles_fetched = {}


def get_all_revisions(title: str) -> list:
    """
    Repeatedly sends requests to API to get ALL revision data
    """
    logging.debug(f"Getting revisions for title: {title}")

    PARAMS = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "flags|timestamp|userid|size|comment|tags|content",
        "rvslots": "main",
        "rvlimit": "max",  # 50 when contents requested, 500-5000 otherwise
        "formatversion": "2",
        "format": "json",
        "maxlag": "2",  # lower is nicer, should be lower than 5
    }

    R = _S.get(url=_API, params=PARAMS)
    DATA = R.json()

    if not is_valid_response(DATA):
        return None

    # there should be a single page in the response
    revisions = DATA["query"]["pages"][0]["revisions"]

    report_progress(len(revisions))

    # presence of a "continue" key denotes an unfinished query
    while "continue" in DATA:

        # modify parameters to include "rvcontinue" value from the last query
        PARAMS.update({"rvcontinue": DATA["continue"]["rvcontinue"]})

        R = _S.get(url=_API, params=PARAMS)
        DATA = R.json()

        if not is_valid_response(DATA):
            return None

        revisions += DATA["query"]["pages"][0]["revisions"]

        report_progress(len(revisions))
    
    logging.info(f"Received {len(revisions)} revisions for page: {title}")

    return revisions


def is_valid_response(data):
    """
    Checks the response from wikipedia revision API for errors and warnings.
    Returns False on error; otherwise returns True.
    """
    if "error" in data:
        logging.error("API reported an error: %s", json.dumps(data, indent=4))
        return False

    if "warning" in data:
        logging.warning("API reported a warning: %s", json.dumps(data, indent=4))
    
    return True


def save_page(page, filename):
    """
    Saves a page to disk. A page is a dict with two keys: "title" and "revisions"
    """
    with open(filename, 'w+') as f:
        json.dump(page, f)
        f.write('')
        logging.info("Page revision data saved to file: \"%s\"", filename)


def count_reverts(revisions):
    count = 0
    for i in revisions:
        # print(i["tags"])
        for q in i["tags"]:
            if q == 'mw-undo' or q == 'mw-reverted' or q == 'Reverted' or q == 'mw-manual-revert':
                count = count + 1
    return count


def report_progress(i):
    print(f"Progress: {i} items", end='\r')


def add_benchmarking(func):
    """
    Adds benchmarking to any function
    """
    @functools.wraps(func)
    def benchmarked(* args, ** kwargs):
        start_time = time.time()
        value = func(* args, ** kwargs)
        end_time = time.time()
        logging.debug(f"Completed call to {func.__name__} in {end_time - start_time:.2f} seconds.")
        return value
    return benchmarked


def save_titles_fetched():
    with open("titles_fetched.json", "w+") as f:
        json.dump(_titles_fetched, f)
        f.write("")
        logging.debug("Saved titles_fetched.json")


def main():
    global _titles_fetched

    logging.info("Script started.")

    with open("titles.json", "r") as f:
        titles = json.load(f)
    
    os.chdir("dataset")
    try:
        with open("titles_fetched.json", 'r') as f:
            _titles_fetched = json.load(f)
    except FileNotFoundError:
        _titles_fetched = {}

    print("Press CTRL-C at any point to stop the script.")

    get_all_revisions_benchmarked = add_benchmarking(get_all_revisions)

    for index, title in enumerate(titles):
        
        # do we have the data for this page already?
        if title in _titles_fetched:
            continue

        revisions = get_all_revisions_benchmarked(title)

        if not revisions:
            break
        print(f"Received {len(revisions)} revisions for page: {title}")
        
        filename = str(index) + ".json"
        save_page({"page" : title, "revisions": revisions}, filename)
        _titles_fetched[title] = filename
        save_titles_fetched()
    
    print("Done.")



if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)-8s %(name)-15s %(message)s",
                filename="mediawiki_extractor.log", level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    try:
        main()
    except KeyboardInterrupt:
        logging.info("User requested to stop the script via keyboard interrupt.")
        save_titles_fetched()
        sys.exit(0)