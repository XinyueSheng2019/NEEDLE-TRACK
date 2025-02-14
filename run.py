#!/usr/bin/env python3
"""
NEEDLE-TRACK: Transient Recognition, Annotation, and Classification Kit

This Python program provides:
  - Local system management with a configuration-friendly setup.
  - An SQLite database to store transient objects along with changeable tags, user comments, and status flags.
  - A command-line interface (CLI) for ingestion, searching, commenting, and listing updated objects.
  - A simulated ingestion routine that reads data exported in JSON format.
  
Future improvements (but not adding new functions):
  - Cloud migration support.
  - Additional user commands.
  - slack robot for notification
"""

import sqlite3
import json
import argparse
from datetime import datetime

# --------------------------
# Database Manager Component
# --------------------------
class DatabaseManager:
    def __init__(self, db_path='needle_track.db', initialize=False):
        # Connect to SQLite database (creates file if not exists)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        self.create_table(initialize)

    def initialize_table(self):
        self.conn.execute('DROP TABLE IF EXISTS transients')
        self.conn.commit()

    def create_table(self, initialize=False):
        # Create a table to store transient objects with various status flags.
        if initialize:
            self.conn.execute('DROP TABLE IF EXISTS transients')
            self.conn.commit()
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS transients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objectId TEXT UNIQUE,
            properties TEXT,
            tags TEXT,
            comments TEXT,
            astronote_status INTEGER DEFAULT 0, -- 0: false, 1: true
            link TEXT,
            is_followup INTEGER DEFAULT 0,
            is_new INTEGER DEFAULT 1,
            is_removed INTEGER DEFAULT 0,
            is_updated INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        '''
        self.conn.execute(create_table_sql)
        self.conn.commit()


    def add_or_update_transient(self, record):
        """
        Insert a new transient or update an existing record if overlap is detected.
        The record is expected to be a dictionary with keys:
            - objectId (str)
            - properties (dict)
            - tags (list) [optional]
            - link (str) [optional]
        """
        now = datetime.now().isoformat()
        cur = self.conn.execute('SELECT * FROM transients WHERE objectId = ?', (record['objectId'],))
        existing = cur.fetchone()
        if existing:
            # Convert stored JSON properties to dictionary for comparison.
            existing_properties = json.loads(existing['properties'])
            if existing_properties != record['properties']:
                # Data has changed; update record and mark as updated.
                new_properties = json.dumps(record['properties'])
                new_tags = json.dumps(record.get('tags', []))
                self.conn.execute('''
                    UPDATE transients
                    SET properties = ?, tags = ?, link = ?, is_updated = 1, updated_at = ?
                    WHERE objectId = ?
                ''', (new_properties, new_tags, record.get('link', ''), now, record['objectId']))
                self.conn.commit()
                return 'updated'
            else:
                return 'no_change'
        else:
            # Insert new record.
            properties_json = json.dumps(record['properties'])
            tags_json = json.dumps(record.get('tags', []))
            comments_json = json.dumps(record.get('comments', []))
            self.conn.execute('''
                INSERT INTO transients (objectId, properties, tags, comments, link, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (record['objectId'], properties_json, tags_json, comments_json, record.get('link', ''), now, now))
            self.conn.commit()
            return 'inserted'

    def mark_as_removed(self, objectId):
        """Mark a transient as removed."""
        now = datetime.now().isoformat()
        self.conn.execute('''
            UPDATE transients
            SET is_removed = 1, updated_at = ?
            WHERE objectId = ?
        ''', (now, objectId))
        self.conn.commit()

    def add_comment(self, objectId, comment):
        """
        Add a comment to the transient with the given ZTF ID.
        Comments are stored as a JSON list of dictionaries containing the comment text and timestamp.
        """
        cur = self.conn.execute('SELECT comments FROM transients WHERE objectId = ?', (objectId,))
        row = cur.fetchone()
        if row:
            try:
                comments = json.loads(row['comments'])
            except json.JSONDecodeError:
                comments = []
            comments.append({'comment': comment, 'timestamp': datetime.now().isoformat()})
            new_comments = json.dumps(comments)
            self.conn.execute('UPDATE transients SET comments = ?, updated_at = ? WHERE objectId = ?',
                              (new_comments, datetime.now().isoformat(), objectId))
            self.conn.commit()
            return True
        return False

    def search_by_id(self, objectId):
        """Retrieve a transient by its unique ZTF ID."""
        cur = self.conn.execute('SELECT * FROM transients WHERE objectId = ?', (objectId,))
        return cur.fetchone()

    def search_by_tag(self, tag):
        """
        Retrieve transients whose tags contain the specified substring.
        (Since tags are stored as JSON, a simple LIKE search is used.)
        """
        cur = self.conn.execute('SELECT * FROM transients WHERE tags LIKE ?', ('%' + tag + '%',))
        return cur.fetchall()

    def search_by_astronote(self, has_astronote=True):
        """Retrieve transients based on their astronote (annotation) status."""
        status = 1 if has_astronote else 0
        cur = self.conn.execute('SELECT * FROM transients WHERE astronote_status = ?', (status,))
        return cur.fetchall()

    def search_updates(self):
        """Retrieve transients that have been updated (are in the Update List)."""
        cur = self.conn.execute('SELECT * FROM transients WHERE is_updated = 1')
        return cur.fetchall()

# --------------------------
# Data Ingestion Component
# --------------------------
def convert_data_scheme(record=dict):
    """
    Convert the data scheme to the required format.
    """
    objectId = record['objectId']
    properties = record.pop('objectId')
    link = 'https://lasair-ztf.lsst.ac.uk/objects/%s/' % objectId
    return {'objectId': objectId, 'properties': properties, 'link': link}
    


def ingest_data(db_manager, json_file, date_range=None):
    """
    Ingest data from a JSON file and update the database.
    The JSON file should contain a list of records.
    
    For each record:
      - If an object with the same ZTF ID exists, compare properties.
      - Update if differences are found and log the update.
      - Otherwise, insert as a new record.
    
    A simple report is printed at the end.
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    report = {'inserted': 0, 'updated': 0, 'no_change': 0}
    for record in data:
        record = convert_data_scheme(record)
        result = db_manager.add_or_update_transient(record)
        if result == 'inserted':
            report['inserted'] += 1
        elif result == 'updated':
            report['updated'] += 1
        else:
            report['no_change'] += 1

    print("Ingestion Report:")
    print(json.dumps(report, indent=2))

# --------------------------
# Command-line Interface (CLI)
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="NEEDLE-TRACK: Transient Recognition Tool")
    subparsers = parser.add_subparsers(dest='command', help="Available commands") 

    # Command to ingest data from a JSON file.
    ingest_parser = subparsers.add_parser('ingest', help="Ingest data from JSON file")
    ingest_parser.add_argument('json_file', help="Path to the JSON file with transient data")
    

    # Command to search for transients.
    search_parser = subparsers.add_parser('search', help="Search transients")
    search_parser.add_argument('--objectId', help="Search by ZTF ID")
    search_parser.add_argument('--tag', help="Search by tag")
    search_parser.add_argument('--astronote', action='store_true', help="Search for objects with an astronote annotation")

    # Command to add a comment to a transient.
    comment_parser = subparsers.add_parser('comment', help="Add a comment to a transient")
    comment_parser.add_argument('objectId', help="ZTF ID of the transient")
    comment_parser.add_argument('comment', help="The comment text")

    # Command to list updated objects.
    ingest_parser.add_argument('initialize', action='store_false', help="Delete all data in the database and initialize a new one")
    updates_parser = subparsers.add_parser('updates', help="List transients that have been updated")

    args = parser.parse_args()
    db_manager = DatabaseManager(initialize=args.initialize)

    if args.command == 'ingest':
        ingest_data(db_manager, args.json_file)
    elif args.command == 'search':
        if args.objectId:
            result = db_manager.search_by_id(args.objectId)
            if result:
                print(dict(result))
            else:
                print("No record found for ZTF ID:", args.objectId)
        elif args.tag:
            results = db_manager.search_by_tag(args.tag)
            for row in results:
                print(dict(row))
        elif args.astronote:
            results = db_manager.search_by_astronote(True)
            for row in results:
                print(dict(row))
        else:
            print("Please provide a search parameter (--objectId, --tag, or --astronote).")
    elif args.command == 'comment':
        success = db_manager.add_comment(args.objectId, args.comment)
        if success:
            print("Comment added successfully to ZTF ID:", args.objectId)
        else:
            print("Record not found for ZTF ID:", args.objectId)
    elif args.command == 'updates':
        results = db_manager.search_updates()
        for row in results:
            print(dict(row))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
