import difflib
import json
import re
import os


os.chdir('dataset')
with open("1.json", 'r') as f:
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