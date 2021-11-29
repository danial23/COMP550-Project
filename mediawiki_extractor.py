# Nov. 25th 2021
# Molly Jacobsen

# Sample script using wikimedia API to extract data into CSV files

import requests
import json
import time
import mwparserfromhell


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

    # "continue" field marks unfinished query
    while "continue" in DATA:

        # modify parameters to include last query's rvcontinue
        PARAMS.update({"rvcontinue": DATA["continue"]["rvcontinue"]})

        R = S.get(url=API, params=PARAMS)
        DATA = R.json()

        if "error" in DATA or "warning" in DATA:
            print(json.dumps(DATA, indent=4))
            return None

        PAGE = DATA["query"]["pages"][0]

        # append to the revision list
        revisions += PAGE["revisions"]

    end_time = time.time()  # for benchmarking

    print("Total time for page \"" + title + "\":", end_time - start_time)  # for benchmarking
    print("Total revisions:", len(revisions))  # for benchmarking

    return revisions


def main():
    revisions = get_all_revisions("SQLite")
    count = count_reverts(revisions)
    process_revision_contents(revisions)
    print("Reverted count:", count)
    print("Revision plaintext example:\n", revisions[-1]["slots"]["main"]["content"])


def save_revisions(revisions, filename):
    with open(filename, 'w') as f:
        for i in revisions:
            f.write("%s\n" % i)


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



if __name__ == "__main__":
    main()