import pandas as pd
from datetime import datetime
from datetime import timedelta
import logging
import matplotlib.pyplot as plt
import sys

sys.path.append('./')

def add_delayed(df):
    """
    Add col Delayed. 0 = punctual, 1 = delayed by more than 10 min
    """
    _df = df.copy()
    delayed = []
    for index, row in _df.iterrows():
        if row['Timedelta'] > 10:
            delayed.append(1)
        else:
            delayed.append(0)
    _df['Delayed'] = delayed
    return _df

def get_punctuality_by(col):
    punctual_df = pd.DataFrame(columns = [col, 'Delayed pct', 'median Delay', "mean Delay", "Occurrences"])
    punctual_df[col] = df[col].unique()

    occDict = dict(df[col].value_counts())

    delays = []
    delayMedian = []
    delayMean = []
    occ = []
    for val in list(punctual_df[col]):
        occ.append(occDict[val])
        delays.append(round(df[df[col] == val]['Delayed'].mean() * 100, 2))
        delayMedian.append(round(df[(df[col] == val) & (df['Delayed'] == 1)]['Timedelta'].median(), 2))
        delayMean.append(round(df[(df[col] == val) & (df['Delayed'] == 1)]['Timedelta'].mean(), 2))
    punctual_df['Delayed pct'] = delays
    punctual_df['median Delay'] = delayMedian
    punctual_df['mean Delay'] = delayMean
    punctual_df['Occurrences'] = occ

    return punctual_df.sort_values(['Delayed pct'])


df = pd.read_csv('assets/data_prep_majority.txt', sep="\t", encoding="utf-8")
df = add_delayed(df)

for cat in ['Carrier_Name', 'Equipment_Type', 'Origin_Code', 'Destination_Code', 'Flight', 'ETD_Group']:
    out_df = get_punctuality_by(cat)
    out_df.to_csv('assets/df_punctuality_by_' + cat + '.csv', sep="\t", encoding="utf-8", index=False)