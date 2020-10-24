import pandas as pd
from datetime import datetime
from datetime import timedelta
import logging
import matplotlib.pyplot as plt
import sys

def clean_data(df):
    """
    Clean data rows, such as invalid characters, NaN, Landed ...
    """
    _df = df.copy()
    logging.warning(f'Received df of len {len(_df)}...')
    for _ in ['Origin', 'Destination', 'Equipment']:
        _df = _df[_df[_].str.contains("\)")]
    for _ in ['Flight Time', 'ETD', 'ATD', 'ETA', 'ATA']:
        _df = _df[~(_df[_].str.contains("-")) & ~(_df[_].str.contains("—"))]
    _df = _df[(_df['ATA'].str.contains("Landed"))]
    _df['ATA'] = _df['ATA'].str.replace('Landed ','')
    _df['ATA'] = _df['ATA'].str.replace(u'Landed\xa0','')
    logging.warning(f'Returned df of len {len(_df)}...')
    return _df

def clean_codes(df):
    """
    Clean airport and equipment codes
    """
    _df = df.copy()
    for _ in ['Origin', 'Destination']:
        _df[[f'{_}_City', f'{_}_Code']] = _df[_].str.split(u"\xa0\(", n = 1, expand = True)
    _df[['Equipment_Type', 'Equipment_Reg']] = _df['Equipment'].str.split(u"\xa0\(", n = 1, expand = True)
    for _ in ['Equipment_Reg', 'Origin_Code', 'Destination_Code']:
        _df[_] = _df[_].str.replace(")", "")
    return _df[['Flight', 'Date', 'Equipment_Type', 'Equipment_Reg', 'Origin_City', 'Origin_Code', 'Destination_City', 'Destination_Code', 'Flight Time', 'ETD', 'ETA', 'ATD', 'ATA']]

def get_carrier_code(df):
    """
    Get carrier codes
    """
    _df = df.copy()
    carrier = {}
    carrier_list = []
    for index, row in _df.iterrows():
        if row['Flight'][:2] not in carrier.keys():
            carrier[row['Flight'][:2]] = ""
        carrier_list.append(row['Flight'][:2])
    return carrier, carrier_list

def set_carrier_info(df, carrier, carrier_class, carrier_list):
    """
    Assign airlines names + class
    """
    _df = df.copy()
    _df['Carrier_Name'] = carrier_list
    _df['Carrier_Name'] = _df['Carrier_Name'].map(carrier)
    _df['Carrier_Class'] = _df['Carrier_Name'].map(carrier_class)
    return _df

def detect_dates(df):
    """
    Detect dates and reformat it
    """
    _df = df.copy()
    date_list = []
    for index, row in _df.iterrows():
        date_list.append(datetime.strptime(row['Date'], '%d-%b-%y').date().strftime('%Y-%m-%d'))
    _df['Date'] = date_list
    return _df

def get_time_delta(df):
    """
    Calculate time deltas
    """
    _df = df.copy()
    deltas = []
    for index, row in _df.iterrows():
        tdelta = datetime.strptime(row['ATA'], '%H:%M') - datetime.strptime(row['ETA'], '%H:%M')
        if datetime.strptime(row['ATA'], '%H:%M') < datetime.strptime(row['ETA'], '%H:%M'):
            deltas.append(-1 * int((datetime.strptime('00:00', '%H:%M') - tdelta).time().minute))
        else:
            deltas.append(int((datetime.strptime('00:00', '%H:%M') + tdelta).time().minute))
    _df['Timedelta'] = deltas
    return _df

def get_departure_groups(df):
    """
    Detect different departure groups throughout the day
    """
    _df = df.copy()
    dep_groups = []
    for index, row in _df.iterrows():
        if datetime.strptime(row['ETD'], '%H:%M') <= datetime.strptime('07:30', '%H:%M'):
            dep_groups.append('Red Eye')
        elif datetime.strptime(row['ETD'], '%H:%M') <= datetime.strptime('12:00', '%H:%M'):
            dep_groups.append('Morning')
        elif datetime.strptime(row['ETD'], '%H:%M') <= datetime.strptime('18:00', '%H:%M'):
            dep_groups.append('Afternoon')
        elif datetime.strptime(row['ETD'], '%H:%M') <= datetime.strptime('21:30', '%H:%M'):
            dep_groups.append('Evening')
        elif datetime.strptime(row['ETD'], '%H:%M') <= datetime.strptime('23:59', '%H:%M'):
            dep_groups.append('Night')
        else:
            dep_groups.append(None)
            logging.warning('invalid time?')
    _df['ETD_Group'] = dep_groups
    return _df

def vote_majority_flight(df):
    """
    Majority vote of flights when they have an unusual leg, so that we only keep the "real" flights
    """
    _df = df.copy()
    flight_filtered = pd.DataFrame()
    flight_list = list(df.Flight.drop_duplicates())
    logging.warning(f'Loaded {len(flight_list)} flights.')
    # Loop through flight list and find major flight
    for flight in flight_list:
        _flight = _df[(_df['Flight'] == flight)].groupby(['Flight', 'Origin_City', 'Destination_City']).describe().sort_values(('Timedelta', 'count'), ascending=False).reset_index()[['Flight', 'Origin_City', 'Destination_City']].head(1)
        flight_filtered = flight_filtered.append(_flight)
    flight_filtered = flight_filtered.reset_index(drop=True).droplevel(0, axis=1)
    flight_filtered.columns = ['Flight', 'Origin_City', 'Destination_City']
    return flight_filtered

def extract_major_flight(flight_filtered, df):
    """
    Majority vote of flights when they have an unusual leg, so that we only keep the "real" flights
    """
    _df = pd.DataFrame()
    for index, row in flight_filtered.iterrows():
        df_temp = df[(df['Flight'] == row['Flight']) & (df['Origin_City'] == row['Origin_City']) & (df['Destination_City'] == row['Destination_City'])]
        _df = _df.append(df_temp)
    return _df

def correct_flighttimes(df):
    _df = df.copy()
    ATA = []
    ETA = []
    ETD = []
    ATD = []
    for index, row in _df.iterrows():
        if row['Destination_City'] in ['Dublin', 'London']:
            ATA.append((datetime.strptime(row['ATA'], '%H:%M') + timedelta(hours = 1)).strftime('%H:%M'))
            ETA.append((datetime.strptime(row['ETA'], '%H:%M') + timedelta(hours = 1)).strftime('%H:%M'))
        elif row['Destination_City'] == "Addis Ababa":
            ATA.append((datetime.strptime(row['ATA'], '%H:%M') - timedelta(hours = 1)).strftime('%H:%M'))
            ETA.append((datetime.strptime(row['ETA'], '%H:%M') - timedelta(hours = 1)).strftime('%H:%M'))
        else:
            ATA.append(row['ATA'])
            ETA.append(row['ETA'])
        if row['Origin_City'] in ['Dublin', 'London']:
            ETD.append((datetime.strptime(row['ETD'], '%H:%M') - timedelta(hours = 1)).strftime('%H:%M'))
            ATD.append((datetime.strptime(row['ATD'], '%H:%M') - timedelta(hours = 1)).strftime('%H:%M'))
        elif row['Destination_City'] == "Addis Ababa":
            ETD.append((datetime.strptime(row['ETD'], '%H:%M') + timedelta(hours = 1)).strftime('%H:%M'))
            ATD.append((datetime.strptime(row['ATD'], '%H:%M') + timedelta(hours = 1)).strftime('%H:%M'))
        else:
            ETD.append(row['ETD'])
            ATD.append(row['ATD'])
    _df['ATA'] = ATA
    _df['ETA'] = ETA
    _df['ETD'] = ETD
    _df['ATD'] = ATD
    # Kick out useless 
    _df = _df[[datetime.strptime(time, '%H:%M') > datetime.strptime('06:30', '%H:%M') for time in list(_df['ATA'])]]
    return _df



carrier = {
    'LH': ['Lufthansa', 0],
    'BA': ['British Airways'],
    'LO': ['LOT', 0],
    'SK': ['SAS', 0],
    'UX': ['Air Europa', 0],
    'IB': ['Iberia', 0],
    'KL': ['KLM Royal Dutch Airlines', 0],
    'DY': ['Norwegian', 1],
    'ET': ['Ethiopian', 0],
    'FR': ['Ryanair', 1],
    'HV': ['Transavia', 1],
    'VY': ['Vueling', 1],
    'EI': ['Aer Lingus', 0],
    'U2': ['EasyJet', 1]
    }

carrier = {
    'LH': 'Lufthansa',
    'BA': 'British Airways',
    'LO': 'LOT',
    'SK': 'SAS',
    'UX': 'Air Europa',
    'IB': 'Iberia',
    'KL': 'KLM Royal Dutch Airlines',
    'DY': 'Norwegian',
    'ET': 'Ethiopian',
    'FR': 'Ryanair',
    'HV': 'Transavia',
    'VY': 'Vueling',
    'EI': 'Aer Lingus',
    'U2': 'EasyJet'
    }

carrier_class = {
    'Lufthansa': 0,
    'British Airways': 0,
    'LOT': 0,
    'SAS': 0,
    'Air Europa': 0,
    'Iberia': 0,
    'KLM Royal Dutch Airlines': 0,
    'Norwegian': 1,
    'Ethiopian': 0,
    'Ryanair': 1,
    'Transavia': 1,
    'Vueling': 1,
    'Aer Lingus': 0,
    'EasyJet': 1
    }