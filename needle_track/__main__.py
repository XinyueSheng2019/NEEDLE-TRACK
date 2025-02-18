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
import os
from pathlib import Path

from needle_track.database_manager import DatabaseManager
from needle_track.data_injest import ingest_data


# --------------------------
# Command-line Interface (CLI)
# --------------------------
def main():
    # Get the directory where the database should be stored
    db_dir = Path.home() / '.needle_track'
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / 'needle_track.db'

    parser = argparse.ArgumentParser(description="NEEDLE-TRACK: Transient Recognition Tool")
    parser.add_argument('-i', '--initialize', action='store_true', default=False, 
                       help="Delete all data in the database and initialize a new one")
    parser.add_argument('--db', default=str(db_path),
                       help="Path to the database file (default: ~/.needle_track/needle_track.db)")

    subparsers = parser.add_subparsers(dest='command', help="Available commands") 

    # Command to ingest data from JSON files
    ingest_parser = subparsers.add_parser('ingest', help="Ingest data from JSON files")
    ingest_parser.add_argument('--slsn', dest='json_file_slsn', 
                              help="Path to the JSON file with SLSN data")
    ingest_parser.add_argument('--tde', dest='json_file_tde',
                              help="Path to the JSON file with TDE data")
    
    # Command to search for transients.
    search_parser = subparsers.add_parser('search', help="Search transients")
    search_parser.add_argument('-o', '--objectId', help="Search by ZTF ID")
    search_parser.add_argument('-f', '--followup', action='store_true', 
                             help="Search for objects with a followup annotation")
    search_parser.add_argument('-s', '--snoozed', action='store_true',
                             help="Search for objects with a snoozed annotation")
    search_parser.add_argument('-a', '--astronote', action='store_true',
                             help="Search for objects with an astronote annotation")


    # Command to add a comment to a transient.
    comment_parser = subparsers.add_parser('comment', help="Add a comment to a transient")
    comment_parser.add_argument('-o', '--objectId', required=True,
                              help="ZTF ID of the transient")
    comment_parser.add_argument('-c', '--comment', required=True,
                              help="The comment text")

    # Command to list updated objects.
    updates_parser = subparsers.add_parser('update', help="List transients that have been updated")
    updates_parser.add_argument('-o', '--objectId', required=True,
                              help="ZTF ID of the transient")
    updates_parser.add_argument('-f', '--followup', action='store_true',
                              help="List transients with followup annotation")
    updates_parser.add_argument('-s', '--snoozed', action='store_true',
                              help="List transients with snoozed annotation")
    updates_parser.add_argument('-a', '--astronote', action='store_true',
                              help="List transients with astronote annotation")

    updates_parser.add_argument('-nf', '--no_followup', action='store_false',
                              help="List transients without followup annotation")
    updates_parser.add_argument('-ns', '--no_snoozed', action='store_false',
                              help="List transients without snoozed annotation")
    updates_parser.add_argument('-na', '--no_astronote', action='store_false',
                              help="List transients without astronote annotation")
    
    args = parser.parse_args()
    
    try:
        db_manager = DatabaseManager(db_path=args.db, initialize=args.initialize)
        print(f"Connected to database at {args.db}")
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return

    if args.command == 'ingest':
        if args.json_file_slsn:
            ingest_data(db_manager, args.json_file_slsn, 'SLSN')
        if args.json_file_tde:
            ingest_data(db_manager, args.json_file_tde, 'TDE')
    elif args.command == 'search':
        if args.objectId:
            result = db_manager.search_by_id(args.objectId)
            if result:
                print(result)
            else:
                print("No record found for ZTF ID:", args.objectId)
        elif args.followup:
            results = db_manager.search_by_followup(True)
            for row in results:
                print(dict(row))
        elif args.snoozed:
            results = db_manager.search_by_snoozed(True)
            for row in results:
                print(dict(row))
        elif args.astronote:
            results = db_manager.search_by_astronote(True)
            for row in results:
                print(dict(row))
        else:
            print("Please provide a search parameter (--objectId, --followup, --snoozed, or --astronote).")
    elif args.command == 'comment':
        success = db_manager.add_comment(args.objectId, args.comment)
        if success:
            print("Comment added successfully to ZTF ID:", args.objectId)
        else:
            print("Record not found for ZTF ID:", args.objectId)
    elif args.command == 'update':
        if args.followup:
            result = db_manager.mark_as_followup(args.objectId)
            if result == 'success':
                print("Followup annotation added successfully to ZTF ID:", args.objectId)
            else:
                print("Error adding followup annotation to ZTF ID:", args.objectId)
        elif args.snoozed:
            result = db_manager.mark_as_snoozed(args.objectId)
            if result == 'success':
                print("Snoozed annotation added successfully to ZTF ID:", args.objectId)
            else:
                print("Error adding snoozed annotation to ZTF ID:", args.objectId)
            
        elif args.astronote:
            result = db_manager.mark_as_astronote(args.objectId)
            if result == 'success':
                print("Astronote annotation added successfully to ZTF ID:", args.objectId)
            else:
                print("Error adding astronote annotation to ZTF ID:", args.objectId)
            
        else:
            results = db_manager.search_updates()
            for row in results: 
                print(dict(row))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
