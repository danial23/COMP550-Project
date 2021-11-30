# Nov. 25th 2021
# Molly Jacobsen
# Danial Motamedi Mehr
# Tigran Ionnisian

# Data collection script

import requests
import threading
import json
import time
import mwparserfromhell
import msvcrt
import os


STOP_KEY = b'q' # pressing q will stop the script

# when set to true, the program stops executing the script gracefully
global stop_signal
stop_signal = False

S = requests.Session()
S.headers.update({"User-Agent": "script (danialmtmdmhr23@gmail.com)", "Accept-encoding": "gzip"})
API = "https://en.wikipedia.org/w/api.php"


def get_all_revisions(title: str) -> list:
    """
    Repeatedly sends requests to API to get ALL revision data
    """

    start_time = time.time()  # for benchmarking

    # request parameters
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

    # send request
    R = S.get(url=API, params=PARAMS)

    # get json data
    DATA = R.json()

    # print error and exit (use another strategy for a more robust script)
    if "error" in DATA or "warning" in DATA:
        print(json.dumps(DATA, indent=4))
        return None

    # we only have a single page in query
    PAGE = DATA["query"]["pages"][0]
    revisions = PAGE["revisions"]
    process_revision_contents(revisions)

    report_progress(len(revisions))

    # "continue" field marks unfinished query
    # stop_signal is set by the user by pressing the stop key
    while "continue" in DATA and not stop_signal:

        # modify parameters to include last query's rvcontinue
        PARAMS.update({"rvcontinue": DATA["continue"]["rvcontinue"]})

        R = S.get(url=API, params=PARAMS)
        DATA = R.json()

        if "error" in DATA or "warning" in DATA:
            print(json.dumps(DATA, indent=4))
            return None

        PAGE = DATA["query"]["pages"][0]

        revisions_added = PAGE["revisions"]
        process_revision_contents(revisions_added)

        # append to the revision list
        revisions += revisions_added

        report_progress(len(revisions))

    end_time = time.time()  # for benchmarking

    print("\nTotal time for page \"" + title + "\":", end_time - start_time)  # for benchmarking

    return revisions


def save_page(page, filename):
    """
    Saves a page to disk. A page is a dict with two keys: "title" and "revisions"
    """
    with open(filename, 'w+') as f:
        json.dump(page, f)
        f.write('')
        print('Page revision data saved to', filename)


def count_reverts(revisions):
    count = 0
    for i in revisions:
        # print(i["tags"])
        for q in i["tags"]:
            if q == 'mw-undo' or q == 'mw-reverted' or q == 'Reverted' or q == 'mw-manual-revert':
                count = count + 1
    return count


def process_revision_contents(revisions: list)-> None:
    """
    Converts the revision content from wikitext to plaintext

    :param revisions: A list containing all revisions to be processed
    """
    for rev in revisions:
        if "slots" not in rev or "main" not in rev["slots"] or "content" not in rev["slots"]["main"]:
            break
        content = rev["slots"]["main"]["content"]
        parsed_content = mwparserfromhell.parse(content) # parse wikitext
        stripped_content = parsed_content.strip_code() # strip code
        rev["slots"]["main"]["content"] = stripped_content


def report_progress(i):
    print(f"Progress: {i} items", end='\r')



def detect_stop_signal():
    """
    Stops the program when it receives a key stroke that matches STOP_KEY
    """
    while True:
        ch = msvcrt.getch()
        if ch == STOP_KEY:
            print('\n\n*** Quitting script ***\n\n')
            global stop_signal
            stop_signal = True
            exit(0)



def main():
    # load titles
    with open('titles.json', "r") as f:
        titles = json.load(f)

    # change working directory
    os.chdir('dataset')

    # try to load previously fetched titles
    try:
        with open('titles_fetched.json', 'r') as f:
            titles_fetched = json.load(f)
    except FileNotFoundError:
        titles_fetched = {}
    
    
    print("Press Q at any point to stop the script gracefully.")


    for index, title in enumerate(titles):
        
        # already got the rev data from this page
        if title in titles_fetched:
            continue
        
        revisions = get_all_revisions(title)

        # dont save if we get interrupted
        if stop_signal:
            break

        # null check (there was an error in the request response)
        if not revisions:
            break
        
        # save rev data to disk
        save_page({"page" : title, "revisions": revisions}, str(index) +'.json')

        # update and save titles_fetched
        titles_fetched[title] = index
        with open('titles_fetched.json', 'w+') as f:
            json.dump(titles_fetched, f)
            f.write('')
    
    print("Done.")



if __name__ == "__main__":
    
    # this thread just waits for the STOP_KEY key stroke (set at top of the script)
    wait_thread = threading.Thread(name='wait_for_quit_key', target=detect_stop_signal)

    # main work thread
    main_thread = threading.Thread(name='script_main', target=main)

    wait_thread.start()
    main_thread.start()