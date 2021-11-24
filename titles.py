# Collects and saves titles of every featured article as a json object containing an array of strings

import requests
import re
import json


if __name__ == '__main__':
    response = requests.get('https://en.wikipedia.org/wiki/Wikipedia:Featured_articles')

    # decode the response content first, with using the specified encoding
    content = response.content.decode(response.encoding)

    # find start and end of the list
    start = content.index('Architecture and archaeology')
    end = content.index('Cleanup listing')

    # create pattern to extract article titles
    m = re.compile('<a href=\"/wiki/(?:.*?)\" title=\"(.*?)\">')
    titles = m.findall(content, start, end)
    print('Extracted', len(titles), 'article titles.')

    # save as a .json file
    with open('titles.json', 'w+') as f:
        json.dump(titles, f)
        f.write('') # the script acts weird without this line
    print('Titles dumped to titles.json')