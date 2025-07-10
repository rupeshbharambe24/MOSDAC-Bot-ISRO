import sqlite3
from pathlib import Path
import json
from typing import Dict, Any
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageHandler:
    @classmethod
    def init_db(cls):
        """Initialize the database"""
        conn = sqlite3.connect(Config.DATABASE_URL.replace('sqlite:///', ''))
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            content_type TEXT,
            processed_data TEXT,
            raw_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            content_id INTEGER,
            key TEXT,
            value TEXT,
            FOREIGN KEY(content_id) REFERENCES content(id)
        )
        ''')
        
        conn.commit()
        conn.close()

    @classmethod
    def store_content(cls, url: str, content_type: str, processed_data: Dict[str, Any], raw_path: str):
        """Store processed content in database"""
        try:
            conn = sqlite3.connect(Config.DATABASE_URL.replace('sqlite:///', ''))
            cursor = conn.cursor()
            
            # Insert main content
            cursor.execute('''
            INSERT OR REPLACE INTO content (url, content_type, processed_data, raw_path)
            VALUES (?, ?, ?, ?)
            ''', (url, content_type, json.dumps(processed_data), str(raw_path)))
            
            content_id = cursor.lastrowid
            
            # Insert metadata
            if 'metadata' in processed_data:
                for key, value in processed_data['metadata'].items():
                    if value:  # Skip None/empty values
                        cursor.execute('''
                        INSERT INTO metadata (content_id, key, value)
                        VALUES (?, ?, ?)
                        ''', (content_id, key, str(value)))
            
            conn.commit()
            conn.close()
            
            # Also save processed data to JSON file
            processed_path = Config.PROCESSED_DIR / f"{content_id}.json"
            with open(processed_path, 'w') as f:
                json.dump(processed_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing content {url}: {str(e)}")

# Initialize database on import
StorageHandler.init_db()