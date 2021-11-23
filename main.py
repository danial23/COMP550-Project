# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import wikipedia_histories
import pandas as pd



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    Let_Us_Continue = wikipedia_histories.get_history('Let Us Continue')
    print(Let_Us_Continue)
    print(Let_Us_Continue[240].content)
    print(len(Let_Us_Continue))
    df = pd.DataFrame(Let_Us_Continue)
    df.to_csv('Let_Us_Continue.csv')

    with open('Let_Us_Continue.txt', 'w') as f:
        for i in Let_Us_Continue:
            f.write("%s\n" % i.content)
