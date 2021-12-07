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
_OLDEST_DATE = "2020-07-20T21:06:21Z"

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

    revisions = []

    while True:
        data = _S.get(url=_API, params=PARAMS).json()

        if not _is_valid_response(data):
            return None

        # there should be a single page in the response
        revisions_received = data["query"]["pages"][0]["revisions"]

        if revisions_received[-1]["timestamp"] < _OLDEST_DATE:
            revisions += _without_old_revisions(revisions_received)
            _report_progress(title, len(revisions))
            break

        revisions += revisions_received
        _report_progress(title, len(revisions))

        if "continue" not in data:
            break

        # modify parameters to include "rvcontinue" value from the last query
        PARAMS.update({"rvcontinue": data["continue"]["rvcontinue"]})
    
    print()

    logging.info(f"Received {len(revisions)} revisions for page \"{title}\"")

    return revisions


def _without_old_revisions(revisions):
    """
    Returns a list of revisions not including revisions older than _OLDEST_DATE
    """
    for i in range(len(revisions)):
        if revisions[i]["timestamp"] < _OLDEST_DATE:
            return revisions[:i]
    return revisions


def _report_progress(title, revs):
    print(f"{title} - {revs} revisions", end="\r")


def _is_valid_response(data):
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


def _save_page(page, filename):
    """
    Saves a page to disk. A page is a dict with two keys: "title" and "revisions"
    """
    with open(filename, 'w+') as f:
        json.dump(page, f)
        f.write('')
        logging.info("Page revision data saved to file: \"%s\"", filename)


def _save_titles_fetched():
    with open("titles_fetched.json", "w+") as f:
        json.dump(_titles_fetched, f)
        f.write("")
        logging.debug("Saved titles_fetched.json")


def count_reverts(revisions):
    count = 0
    for i in revisions:
        # print(i["tags"])
        for q in i["tags"]:
            if q == 'mw-undo' or q == 'mw-reverted' or q == 'Reverted' or q == 'mw-manual-revert':
                count = count + 1
    return count


def add_benchmarking(func):
    """
    Adds benchmarking to any function
    """
    @functools.wraps(func)
    def benchmarked(* args, ** kwargs):
        start_time = time.time()
        value = func(* args, ** kwargs)
        end_time = time.time()
        logging.debug(f"Finished call to {func.__name__} in {end_time - start_time:.2f} seconds.")
        return value
    return benchmarked


def _avg_time_per_page():
    """
    Returns a function to report the average time it takes to get all revisions of a page
    """
    PAGE_WINDOW_SIZE = 100
    start_time = time.time()
    page_window = [start_time for _ in range(PAGE_WINDOW_SIZE)]
    page_index = 0
    def report_avg():
        nonlocal start_time, page_window, page_index

        current_time = time.time()
        page_index += 1

        # calculate time/page average
        array_index = (page_index + 1) % PAGE_WINDOW_SIZE - 1
        start_time = page_window[array_index]
        n = min(page_index, PAGE_WINDOW_SIZE)
        avg_time_per_page = (current_time - start_time) / n

        # update window
        page_window[array_index] = current_time

        print(f"Average time per page = {avg_time_per_page:.2f}s")
    return report_avg


def main():
    global _titles_fetched

    logging.info("Script started.")

    with open("titles.json", "r") as f:
        titles = json.load(f)
    
    os.chdir(_DATASET_DIR)

    try:
        with open("titles_fetched.json", 'r') as f:
            _titles_fetched = json.load(f)
    except FileNotFoundError:
        _titles_fetched = {}


    print("Press CTRL-C at any point to stop the script.")
    report_avg_time = _avg_time_per_page()
    for index, title in enumerate(titles):
        
        if title in _titles_fetched:
            continue

        revisions = get_all_revisions(title)

        if not revisions:
            break
        
        filename = str(index) + ".json"
        _save_page({"page" : title, "revisions": revisions}, filename)
        _titles_fetched[title] = filename
        _save_titles_fetched()

        report_avg_time()
    
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
        _save_titles_fetched()
        sys.exit(0)