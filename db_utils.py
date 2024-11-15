import sqlite3
from datetime import datetime
import json
import re

def init_db():
    conn = sqlite3.connect('prompts.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scene_name TEXT,
            input TEXT,
            result TEXT,
            expected TEXT,
            capture_date TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def extract_scene_name(content):
    if isinstance(content, str):
        match = re.search(r'##\s*Scene\s+(\w+)\s+state', content)
        if match:
            return match.group(1)
    return "unknown"

def save_prompt(data, result):
    try:
        # Extract scene name from the system message content
        scene_name = "unknown"
        if 'messages' in data:
            for message in data['messages']:
                if message['role'] == 'system':
                    content = message['content']
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                scene_name = extract_scene_name(item['text'])
                                if scene_name != "unknown":
                                    break
                    else:
                        scene_name = extract_scene_name(content)
                    if scene_name != "unknown":
                        break

        conn = sqlite3.connect('prompts.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO prompts (scene_name, input, result, expected, capture_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            scene_name,
            json.dumps(data),
            result,
            "",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving to database: {e}") 