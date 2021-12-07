import difflib
import json
import re
import os
import mwparserfromhell


def process_revision_contents(revisions)-> None:
    """
    Process all revisions of one page.

    Args:
        revisions: A list containing all revisions to be processed
    """
    for rev in revisions:
        if "slots" not in rev or "main" not in rev["slots"] or "content" not in rev["slots"]["main"]:
            break
        content = rev["slots"]["main"]["content"]
        rev["slots"]["main"]["content"] = _wikitext_to_plaintext(content)


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



def main():
    os.chdir('dataset')
    with open("titles_fetched.json", 'r') as f:
        titles_fetched = json.load(f)


if (__name__ == "__main__"):
    main()