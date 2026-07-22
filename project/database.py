# -*- coding: utf-8 -*-

import sqlite3
from pathlib import Path


class ProjectDatabase:

    def __init__(self, db_path='data/projects.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self):
        return sqlite3.connect(str(self.db_path))

    def init_db(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                project_name TEXT NOT NULL,
                normalized_name TEXT
            )
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_project_code
            ON projects(project_code)
        ''')
        conn.commit()
        conn.close()

    def find_by_code(self, code):
        if not code:
            return None

        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            'SELECT project_code, project_name FROM projects WHERE project_code=? LIMIT 1',
            (code,)
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'project_code': row[0],
            'project_name': row[1]
        }

    def list_all(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            'SELECT project_code, project_name, normalized_name FROM projects'
        )
        rows = cur.fetchall()
        conn.close()

        return [
            {
                'project_code': row[0],
                'project_name': row[1],
                'normalized_name': row[2] or ''
            }
            for row in rows
        ]
