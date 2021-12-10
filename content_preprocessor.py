import difflib
import json
import re
import os
import mwparserfromhell
import pathlib
import logging
import mediawiki_extractor

_BASIC_PROCESSED_DIR = "basic-processed"


def process_page_revisions(page)-> None:
    """
    Process all revisions of one page.

    Args:
        page: A page from the dataset
    """
    previous_plaintext = ""
    for index, rev in enumerate(page["revisions"]):
        title = page["title"]
        if not _revision_has_content(rev):
            logging.warning(f"Revision has no content in main slot: Page \"{title}\" - Revision index \"{index}\"")
            continue
        content = rev["slots"]["main"]["content"]
        plaintext = _wikitext_to_plaintext(content)

        rev["slots"]["main"]["content-plaintext"] = plaintext
        rev["slots"]["main"]["content-diff"] = _content_diff(previous_plaintext, plaintext)

        mediawiki_extractor.report_progress(title, index)

        previous_plaintext = plaintext


def _revision_has_content(rev):
    """
    Does this revision have a main slot with a content key?
    """
    return "slots" in rev and "main" in rev["slots"] and "content" in rev["slots"]["main"]



def _wikitext_to_plaintext(wikitext: str)-> str:
    """
    Parse wikitext and return plaintext
    """
    parsed_content = mwparserfromhell.parse(wikitext) # parse wikitext
    stripped_content = parsed_content.strip_code() # strip code
    return stripped_content


def _content_diff(old_content: str, new_content: str) -> str:
    """
    Returns a string showing diff (git format)
    """

    beforeSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", old_content)))
    afterSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", new_content)))

    diff = difflib.unified_diff(beforeSequence, afterSequence)

    diffString = ""
    for line in diff:
        diffString += line + "\n"
    
    return diffString


def _save_processed_page(page, filename):
    """
    Saves a page to disk. A page is a dict with two keys: "title" and "revisions"
    """
    with open(BASIC_PROCESSED_ABS_PATH.joinpath(filename), 'w+') as f:
        json.dump(page, f)
        f.write('')
        logging.info("Page revision data saved to file: \"%s\"", filename)



def main():
    global BASIC_PROCESSED_ABS_PATH

    logging.info("Script started.")

    BASIC_PROCESSED_ABS_PATH = pathlib.Path(__file__).parent.joinpath(_BASIC_PROCESSED_DIR)
    BASIC_PROCESSED_ABS_PATH.mkdir(exist_ok=True) # create directory if it does not exist
    
    os.chdir('dataset')
    with open("titles_fetched.json", 'r') as f:
        titles_fetched = json.load(f)
    
    report_avg = mediawiki_extractor.avg_time_per_page()
    
    for index, title in enumerate(titles_fetched):
        filename = titles_fetched[title]
        try:
            with open(titles_fetched[title], 'r') as f:
                page = json.load(f)
        except FileNotFoundError:
            continue

        process_page_revisions(page)
        _save_processed_page(page, filename)

        print()
        report_avg()
    
    print()
    print("Done.")



if (__name__ == "__main__"):
    logging.basicConfig(format="%(asctime)s %(levelname)-8s %(name)-15s %(message)s",
            filename="content_preprocessor.log", level=logging.DEBUG)
    main()