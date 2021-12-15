import difflib
import json
import multiprocessing
import concurrent.futures
import re
import os
import mwparserfromhell
import pathlib
import logging
import tqdm
import signal
import logging.handlers
import time

_DATASET_DIR = "dataset"
_BASIC_PROCESSED_DIR = "basic-processed"
_BASIC_PROCESSED_ABS_PATH = pathlib.Path(__file__).parent.joinpath(_BASIC_PROCESSED_DIR)
_REWRITE = False # rewrite files already processed?
_PROGRESS_POSITION = 0

_abort_event = type("DummyEvent", (object, ), {"is_set" : lambda: False})


def process_page_revisions(page, progress_callback=lambda : None)-> None:
    """
    Process all revisions of one page. Flattens the revision structure in the process.

    Args:
        page: A page from the dataset
    """
    global _abort_event

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

        progress_callback()

        if _abort_event.is_set():
            return

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


def process_file(filename: str):
    """
    Process a single file and save results to disk.
    """
    global _BASIC_PROCESSED_ABS_PATH, _abort_event

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

    total = 0 if "revisions" not in page else len(page["revisions"])
    with tqdm.tqdm(desc= f"{filename}", unit="rev", total=total, position=_PROGRESS_POSITION, leave=False) as pbar:
        
        process_page_revisions(page, pbar.update)

        if _abort_event.is_set():
            logging.info(f"Abort set while processing file: {filename}")
            return False

        _save_processed_page(page, filename)

    return True


def _init_worker(logQueue, tqdmLock, count, abort_event):
    global _PROGRESS_POSITION, _abort_event

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(logging.handlers.QueueHandler(logQueue))

    tqdm.tqdm.set_lock(tqdmLock)

    with count:
        count.value += 1
        _PROGRESS_POSITION = count.value

    _abort_event = abort_event

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

    logQueue = multiprocessing.Queue() # thread/process-safe queue
    logQueueListner = logging.handlers.QueueListener(logQueue, handler)
    
    return logQueue, logQueueListner


def _interrupt_handler(signum, stack):
    logging.info("User requested to stop the script via keyboard interrupt.")
    _abort_event.set()


def main(logQueue: multiprocessing.Queue):
    global _BASIC_PROCESSED_ABS_PATH, _abort_event

    logging.info("Script started.")

    _BASIC_PROCESSED_ABS_PATH.mkdir(exist_ok=True) # create directory if it does not exist
    
    os.chdir(_DATASET_DIR)
    with open("titles_fetched.json", 'r') as f:
        titles_fetched = json.load(f)
    
    files = list(titles_fetched.values())
    
    tqdmLock = multiprocessing.RLock()
    tqdm.tqdm.set_lock(tqdmLock)
    count = multiprocessing.Value("i", 0)
    _abort_event = multiprocessing.Event()
    _abort_event.clear()
    pool_initargs = [logQueue, tqdmLock, count, _abort_event]

    with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=pool_initargs) as executor, \
            tqdm.tqdm(desc="Total", unit="page", total=len(files), position=_PROGRESS_POSITION, leave=True) as pbar:

        signal.signal(signal.SIGINT, _interrupt_handler)

        futures = set()

        def future_callback(future):
            nonlocal futures
            nonlocal pbar
            pbar.update()
            futures.remove(future)

        for file in files:
            future = executor.submit(process_file, file)
            futures.add(future)
            future.add_done_callback(future_callback)
        
        pbar.write("You can press Ctrl + C to stop at any point.")

        allJobsDone = True
        # unfinishedJobs = 0
        while futures: # check abort_event periodically
            if _abort_event.is_set():
                # if all(map(lambda future: future.running(), futures)): # are the only remaining jobs all running?
                #     pbar.write("Only a few jobs left. Waiting...")
                #     executor.shutdown(wait=True, cancel_futures=False) # wait for the jobs to finish
                # if futures:
                    allJobsDone = False
                    unfinishedJobs = len(futures)
                    pbar.write(f"Stopping the script gracefully...")
                    pbar.close()
                    executor.shutdown(wait=True, cancel_futures=True)
                    break
            time.sleep(0.5)
        pbar.close()

        if allJobsDone:
            logging.info("All jobs finished successfully.")
            print("\n\nAll jobs finished successfully.\n")
        else:
            logging.info(f"Stopped with {unfinishedJobs} jobs remaining.")
            print(f"\n\nThere are {unfinishedJobs} unfinished jobs.\n")

        executor.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    logQueue, logQueueListner = _init_logger()
    logQueueListner.start()

    main(logQueue)

    logQueueListner.stop()