# import requests
# import lasair
import json 
from datetime import datetime, timedelta
import astropy.time as at


# --------------------------
# Data Ingestion Component
# --------------------------


def download_needle_filter(file_path, date_range=8.0):
    '''
    Download NEEDLE-annotated objects from a JSON file.
    return a dict of NEEDLE-annotated objects within the date range, default is 8 days.
    called twice for SLSN and TDE, separately.
    ''' 
    if file_path is None:
        return []
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    data = [convert_data_scheme(record) for record in data if float(record['days_latest']) <= date_range]

    return data

def convert_date(date_str):
    return at.Time(date_str, format='isot', scale='utc').jd

def convert_data_scheme(record=dict):
    """
    Convert the data scheme to the required format.
    """
    objectId = record['objectId']
    try:    
        classdict = record['classdict']
    except KeyError:
        print("No classdict found for %s" % objectId)

    explanation = record['explanation']
    del record['objectId']
    del record['classdict']
    del record['explanation']
    properties = record
    link = 'https://lasair-ztf.lsst.ac.uk/objects/%s/' % objectId
    return {'objectId': objectId, 'properties': properties, 'link': link, 'classdict': classdict, 'explanation': explanation}
    

def ingest_data(db_manager, file_path, data_type, date_range=8):
    """
    Ingest data from a JSON file and update the database.
    The JSON file should contain a list of records.
    data_range is the number of days to fetch data from Lasair, default is 8 days.
    
    For each record:
      - If an object with the same ZTF ID exists, compare properties.
      - Update if differences are found and log the update.
      - Otherwise, insert as a new record.
    
    A simple report is printed at the end.
    """
    if file_path is None:
        print("Please provide any SLSN or TDE JSON files.")
        raise ValueError("Please provide any SLSN or TDE JSON files.")
    
    data = download_needle_filter(file_path, date_range)

    report = {'inserted': 0, 'updated': 0, 'no_change': 0}
    for record in data:
   
        if 'created_at' in record:
            record['created_at'] = convert_date(record['created_at'])
        if 'updated_at' in record:
            record['updated_at'] = convert_date(record['updated_at'])
            
        result = db_manager.add_or_update_transient(record)
        if result == 'inserted':
            report['inserted'] += 1
        elif result == 'updated':
            report['updated'] += 1
        else:
            report['no_change'] += 1

    print("Ingestion Report for %s:" % data_type)
    print(json.dumps(report, indent=2))
