import difflib
import json
import re
import os
import mwparserfromhell
import pathlib
import logging
from multiprocessing import Pool, Queue
import tqdm
import signal
import logging.handlers

_BASIC_PROCESSED_DIR = "basic-processed"
_BASIC_PROCESSED_ABS_PATH = pathlib.Path(__file__).parent.joinpath(_BASIC_PROCESSED_DIR)
_REWRITE = True # rewrite files already processed?


def process_page_revisions(page)-> None:
    """
    Process all revisions of one page. Flattens the revision structure in the process.

    Args:
        page: A page from the dataset
    """
    previous_content = None
    previous_plaintext = None
    for index, rev in reversed(list(enumerate(page["revisions"]))):
        title = page["title"]
        if not _revision_has_content(rev):
            logging.warning(f"Revision has no content in main slot: Page \"{title}\" - Revision index \"{index}\"")
            rev["slots"]["main"]["content"] = ""

        content = rev["slots"]["main"]["content"]
        plaintext = _wikitext_to_plaintext(content)

        if "slots" in rev:
            del rev["slots"]

        rev["reverted"] = True if "mw-reverted" in rev["tags"] else False
        rev["comment-plaintext"] = _wikitext_to_plaintext(rev["comment"]) if "comment" in rev else ""
        rev["content"] = content
        rev["content-diff"] = "" if previous_content is None else _content_diff(previous_content, content)
        rev["content-plaintext"] = plaintext
        rev["content-plaintext-diff"] = "" if previous_content is None else _content_plaintext_diff(previous_plaintext, plaintext)

        previous_content = content
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
    Returns a string showing diff (git format). Splits content at newlines and new sentences.
    """

    beforeSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", old_content)))
    afterSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", new_content)))

    diff = difflib.unified_diff(beforeSequence, afterSequence)

    diffString = ""
    for line in diff:
        diffString += line + "\n"
    
    return diffString


def _content_plaintext_diff(old_plaintext_content: str, new_plaintext_content: str) -> str:
    """
    Returns a string showing diff (git format). Splits content at newlines and new sentences.
    """

    beforeSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", old_plaintext_content)))
    afterSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", new_plaintext_content)))

    diff = difflib.unified_diff(beforeSequence, afterSequence)

    diffString = ""
    for line in diff:
        diffString += line + "\n"
    
    return diffString


def _save_processed_page(page, filename: str):
    """
    Saves a page to disk. A page is a dict with two keys: "title" and "revisions"
    """
    global _BASIC_PROCESSED_ABS_PATH

    with open(_BASIC_PROCESSED_ABS_PATH.joinpath(filename), 'w+') as f:
        json.dump(page, f)
        f.write('')
        logging.info("Preprocessed revision data saved to file: \"%s\"", filename)


def process_file(filename):
    """
    Process a single file and save results to disk.
    """
    global _BASIC_PROCESSED_ABS_PATH

    if not _REWRITE:
        try:
            with open(_BASIC_PROCESSED_ABS_PATH.joinpath(filename), "r") as f:
                logging.debug(f"Skipped processing of file \"{filename}\" because it is already processed.")
                return True
        except FileNotFoundError:
            pass

    try:
        with open(filename, 'r') as f:
            page = json.load(f)
    except FileNotFoundError:
        logging.warning(f"File {filename} not found.")
        return False

    process_page_revisions(page)
    _save_processed_page(page, filename)

    return True


def _init_worker(logQueue):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(logging.handlers.QueueHandler(logQueue))

    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _init_logger():
    """
    Initialize logging.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    
    handler = logging.FileHandler(filename="content_preprocessor.log")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s %(processName)-20s %(levelname)-8s %(name)-15s %(message)s"))

    root.addHandler(handler)

    logQueue = Queue() # thread/process-safe queue
    logQueueListner = logging.handlers.QueueListener(logQueue, handler)
    
    return logQueue, logQueueListner



def main(logQueue: Queue):
    global _BASIC_PROCESSED_ABS_PATH

    logging.info("Script started.")

    _BASIC_PROCESSED_ABS_PATH.mkdir(exist_ok=True) # create directory if it does not exist
    
    os.chdir('dataset')
    with open("titles_fetched.json", 'r') as f:
        titles_fetched = json.load(f)
    
    files = list(titles_fetched.values())
    
    pool = Pool(processes=None, initializer=_init_worker, initargs=[logQueue])

    try:
        for _ in tqdm.tqdm(pool.imap_unordered(process_file, files), total=len(files)):
            pass
    except KeyboardInterrupt:
        logging.info("User requested to stop the script via keyboard interrupt.")
        print("KeyboardInterrupt: waiting for current jobs to finish before quitting")
    
    pool.close()
    pool.join()


if __name__ == "__main__":
    logQueue, logQueueListner = _init_logger()
    logQueueListner.start()

    main(logQueue)

    logQueueListner.stop()