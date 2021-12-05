import difflib
import json
import re
import os
import mwparserfromhell


def process_revision_contents(revisions: list)-> None:
    """
    Converts the revision content from wikitext to plaintext

    Args:
        revisions: A list containing all revisions to be processed
    """
    for rev in revisions:
        if "slots" not in rev or "main" not in rev["slots"] or "content" not in rev["slots"]["main"]:
            break
        content = rev["slots"]["main"]["content"]
        parsed_content = mwparserfromhell.parse(content) # parse wikitext
        stripped_content = parsed_content.strip_code() # strip code
        rev["slots"]["main"]["content"] = stripped_content



os.chdir("dataset")
with open("1.json", "r") as f:
    data = json.load(f)
beforeString: str = data["revisions"][13]["slots"]["main"]["content"]
afterString: str = data["revisions"][12]["slots"]["main"]["content"]

beforeSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", beforeString)))
afterSequence = list(filter(None, re.split("(.*?\. )|(?:\n)", afterString)))

# seq0 = list(filter(None, re.split('(?: )|(?:\n)', str0)))
# seq1 = list(filter(None, re.split('(?: )|(?:\n)', str1)))

diff = difflib.unified_diff(beforeSequence, afterSequence)

diffString = ""
for line in diff:
    diffString += line + "\n"

print(diffString)