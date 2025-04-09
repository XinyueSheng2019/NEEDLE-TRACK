import sqlite3
import json
from datetime import datetime
from pathlib import Path

# --------------------------
# Database Manager Component
# --------------------------
class DatabaseManager:
    def __init__(self, db_path='needle_track.db', initialize=False):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
            initialize: If True, recreate all tables
        """
        # Convert to Path object for better path handling
        self.db_path = Path(db_path)
        
        # Create parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to SQLite database (creates file if not exists)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        
        if initialize:
            self.initialize_table()
        self.create_table()

    def initialize_table(self):
        self.conn.execute('DROP TABLE IF EXISTS transients')
        self.conn.commit()

    def create_table(self, initialize=False):
        # Create a table to store transient objects with various status flags.
        if initialize:
            self.initialize_table()
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS transients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objectId TEXT UNIQUE,
            properties TEXT,
            comments TEXT,
            link TEXT,
            classdict TEXT,
            explanation TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_astronote INTEGER DEFAULT 0, -- 0: false, 1: true
            is_followup INTEGER DEFAULT 0, -- 0: false, 1: true
            is_new INTEGER DEFAULT 1, -- 0: false, 1: true
            is_updated INTEGER DEFAULT 0, -- 0: false, 1: true
            is_snoozed INTEGER DEFAULT 0  -- 0: false, 1: true
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
            - comments (list)
            - link (str) [optional]
            - classdict (dict)
            - explanation (str)
        """
        now = datetime.now().isoformat()
        cur = self.conn.execute('SELECT * FROM transients WHERE objectId = ?', (record['objectId'],))
        existing = cur.fetchone()
        if existing:
            # Convert Row to dict for easier access
            existing_dict = dict(existing)
            
            # Convert stored JSON properties to dictionary for comparison.
            existing_properties = json.loads(existing_dict['properties'])
            if existing_properties != record['properties']:
                # Data has changed; update record and mark as updated.
                new_properties = json.dumps(record['properties'])
                new_classdict = json.dumps(record['classdict'])
                new_explanation = record['explanation']
                
                # Get values from existing record with defaults
                comments = existing_dict.get('comments', '[]')
                link = existing_dict.get('link', '')
                is_astronote = existing_dict.get('is_astronote', 0)
                is_followup = existing_dict.get('is_followup', 0)
                is_snoozed = existing_dict.get('is_snoozed', 0)
                
                self.conn.execute('''
                    UPDATE transients
                    SET properties = ?, comments = ?, link = ?, classdict = ?, explanation = ?, 
                        is_astronote = ?, is_followup = ?, is_new = ?, is_updated = 1, 
                        is_snoozed = ?, updated_at = ?
                    WHERE objectId = ?
                ''', (new_properties, 
                      comments,
                      link, 
                      new_classdict, 
                      new_explanation, 
                      is_astronote, 
                      is_followup, 
                      0, 
                      is_snoozed, 
                      now, 
                      existing_dict['objectId']))
                self.conn.commit()
                return 'updated'
            else:
                return 'no_change'
        else:
            # Insert new record.
            # Convert dictionaries to JSON strings before storing
            properties_json = json.dumps(record.get('properties', {}))
            classdict_json = json.dumps(record.get('classdict', {}))
            comments_json = json.dumps([])  # Empty list for new records

            self.conn.execute('''
                INSERT INTO transients (objectId, properties, comments, link, classdict, explanation, is_astronote, is_followup, is_new, is_updated, is_snoozed, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('objectId', ''),
                properties_json,
                comments_json,
                record.get('link', ''),
                classdict_json,
                record.get('explanation', ''),
                0, 0, 1, 1, 0, now
            ))
            self.conn.commit()
            return 'inserted'

    def mark_as_snoozed(self, objectId):
        """Mark a transient as snoozed."""
        try:
            now = datetime.now().isoformat()
            self.conn.execute('''
                UPDATE transients
                SET is_snoozed = 1, updated_at = ?, is_followup = 0
                WHERE objectId = ?
            ''', (now, objectId))
            self.conn.commit()
            return 'success'
        except Exception as e:
            print(f"Error marking as snoozed: {e}")
            return 'error'

    def mark_as_followup(self, objectId):
        """Mark a transient as followup."""
        try:
            # First check if object exists
            cur = self.conn.execute('SELECT objectId FROM transients WHERE objectId = ?', (objectId,))
            if not cur.fetchone():
                print(f"Object {objectId} not found in database")
                return 'error'

            now = datetime.now().isoformat()
            self.conn.execute('''
                UPDATE transients
                SET is_followup = 1, is_snoozed = 0, updated_at = ?
                WHERE objectId = ?
            ''', (now, objectId))
            # Verify the update
            cur = self.conn.execute('SELECT is_followup FROM transients WHERE objectId = ?', (objectId,))
            row = cur.fetchone()
            if row and row['is_followup'] == 1:
                self.conn.commit()
                return 'success'
            else:
                print(f"Failed to update followup status for {objectId}")
                return 'error'
                
        except Exception as e:
            print(f"Error marking as followup: {e}")
            return 'error'

    def mark_as_astronote(self, objectId):
        """Mark a transient as astronote."""
        try:
            now = datetime.now().isoformat()
            self.conn.execute('''
                UPDATE transients
                SET is_astronote = 1, is_followup = 1, is_snoozed = 0, updated_at = ?
                WHERE objectId = ?
            ''', (now, objectId))
            self.conn.commit()
            return 'success'
        except Exception as e:
            print(f"Error marking as astronote: {e}")
            return 'error'

    
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
            comments.append(comment + '(%s)' % datetime.now().isoformat())
            new_comments = json.dumps(comments)
            self.conn.execute('UPDATE transients SET comments = ?, updated_at = ? WHERE objectId = ?',
                              (new_comments, datetime.now().isoformat(), objectId))
            self.conn.commit()
            return True
        return False

    def search_all(self):
        """Retrieve all transients."""
        cur = self.conn.execute('SELECT * FROM transients')
        results = []
        for row in cur.fetchall():
            results.append(dict(row))
        return results
    
    def search_by_id(self, objectId):
        """Retrieve a transient by its unique ZTF ID."""
        cur = self.conn.execute('SELECT * FROM transients WHERE objectId = ?', (objectId,))
        row = cur.fetchone()
        if row:  # If we found a record
            result = dict(row)
            # Parse JSON fields
            for field in ['properties', 'classdict', 'comments']:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            return [result]  # Return as list for consistency with other search methods
        return []  # Return empty list if no record found

    def search_by_followup(self, has_followup=True):
        """Retrieve transients based on their followup status."""
        status = 1 if has_followup else 0
        cur = self.conn.execute('SELECT * FROM transients WHERE is_followup = ?', (status,))
        results = []
        for row in cur.fetchall():
            result = dict(row)
            # Parse only JSON fields
            json_fields = ['properties', 'classdict', 'comments']
            for field in json_fields:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        print(f"Error decoding JSON at Field: {field}")
                        result[field] = None  # Set to None if parsing fails
            
            # Keep link as plain string
            result['link'] = str(result.get('link', ''))
            results.append(result)

        return results

    def search_by_astronote(self, has_astronote=True):
        """Retrieve transients based on their astronote (annotation) status."""
        status = 1 if has_astronote else 0
        cur = self.conn.execute('SELECT * FROM transients WHERE is_astronote = ?', (status,))
        results = []
        for row in cur.fetchall():
            result = dict(row)
            # Parse only JSON fields
            json_fields = ['properties', 'classdict', 'comments']
            for field in json_fields:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        print(f"Error decoding JSON at Field: {field}")
                        result[field] = None  # Set to None if parsing fails
            
            # Keep link as plain string
            result['link'] = str(result.get('link', ''))
            results.append(result)
        return results

    def search_by_snoozed(self, has_snoozed=True):
        """Retrieve transients based on their snoozed status."""
        status = 1 if has_snoozed else 0
        cur = self.conn.execute('SELECT * FROM transients WHERE is_snoozed = ?', (status,))
        results = []
        for row in cur.fetchall():
            result = dict(row)
            # Parse only JSON fields
            json_fields = ['properties', 'classdict', 'comments']
            for field in json_fields:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        print(f"Error decoding JSON at Field: {field}")
                        result[field] = None  # Set to None if parsing fails
            
            # Keep link as plain string
            result['link'] = str(result.get('link', ''))
            results.append(result)
        return results
    
    def search_updates(self):
        """Retrieve transients that have been updated (are in the Update List)."""
        cur = self.conn.execute('SELECT * FROM transients WHERE is_updated = 1')
        results = []
        for row in cur.fetchall():
            result = dict(row)
            # Parse only JSON fields
            json_fields = ['properties', 'classdict', 'comments']
            for field in json_fields:
                if result[field]:
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        print(f"Error decoding JSON at Field: {field}")
                        result[field] = None  # Set to None if parsing fails
            
            # Keep link as plain string
            result['link'] = str(result.get('link', ''))
            results.append(result)
        return results
