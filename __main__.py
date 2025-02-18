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

Problems:
1. when update the data, tags, et al are not saved.
2. tag is a list, but it is stored as a string.
3. is_followup, is_new, is_removed, is_updated are not used.
4. SLSN, and TDE are not separated. 
"""

import argparse
from datetime import datetime

from data_injest import auto_ingestion, ingest_data
from database_manager import DatabaseManager


# --------------------------
# Command-line Interface (CLI)
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="NEEDLE-TRACK: Transient Recognition Tool")
    parser.add_argument('-i', '--initialize', action='store_true', default=False, help="Delete all data in the database and initialize a new one")

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
    
    # tag to add a tag to a transient
    tag_parser = subparsers.add_parser('tag', help="Add a tag to a transient.  0: followup, 1: favored, 2: new, 4: removed")
    tag_parser.add_argument('objectId', help="ZTF ID of the transient")
    tag_parser.add_argument('tag', help="followup, favored, new, removed")

    # Command to list updated objects.
    updates_parser = subparsers.add_parser('updates', help="List transients that have been updated")
    # updates_parser.add_argument('updates', action='store_true', help="List transients that have been updated")

    args = parser.parse_args()
    db_manager = DatabaseManager(initialize=args.initialize)

    if args.command == 'ingest':
        ingest_data(db_manager, args.json_file)
    elif args.command == 'search':
        if args.objectId:
            result = db_manager.search_by_id(args.objectId)
            if result:
                print(result)
            else:
                print("No record found for ZTF ID:", args.objectId)
        elif args.tag:
            results = db_manager.search_by_tag(args.tag)
            print(results)
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
    elif args.command == 'tag':
        success = db_manager.add_tag(args.objectId, args.tag)
        if success:
            print("Tag added successfully to ZTF ID:", args.objectId)
        else:
            print("Record not found for ZTF ID:", args.objectId)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
