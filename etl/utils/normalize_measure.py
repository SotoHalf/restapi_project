import csv
import json
import pandas as pd
from pprint import pprint

def remove_nums_by_s(s):
    n_s = ""
    for c in s:
        try:
            float(c)
        except ValueError:
            n_s += c
    return n_s

if __name__ == "__main__":

    measures_names_freq = {}
    df = pd.read_csv("./../../api_extractions/themealdb/raw/2025-12-09.csv")

    for i in range(1, 41):
        col = f'measure_{i}'
        if col not in df.columns:  continue

        list_measures = df[col].fillna('').tolist()
        for m in list_measures:
            if not m:  continue
    
            tokens = m.split()
            for t in tokens:
                t = remove_nums_by_s(t) #remove all nums
                if not t: continue

                t = t.strip().lower()
                if not t: continue

                measures_names_freq.setdefault(t,0)
                measures_names_freq[t] += 1

    sorted_items = sorted( 
        measures_names_freq.items(), 
        key=lambda x: x[1], 
        reverse=True 
    )

    with open('measures_data_freq.json', 'w', encoding='utf-8') as file:
        json.dump(
            {"freq": sorted_items},
            file,
            ensure_ascii=False,
            indent=2
        )

    with open('measures_strings.json','w', encoding='utf-8') as file:
        json.dump({"measure_strings": [x for x,y in sorted_items]},
            file,
            ensure_ascii=False,
            indent=2 
        )

    '''

    GET MEASURES JSON

    for i in range(1,41):
        col = f'measure_{i}'
        if col in df.columns:
            list_measures = df[f'measure_{i}'].fillna('').tolist()
            for m in list_measures:
                if not m: continue
                measures.add(m)

    with open('measures_data.json','w', encoding='utf-8') as file:
        json.dump({"measure_values": list(measures)},
            file,
            ensure_ascii=False,
            indent=2 
        )

    '''



