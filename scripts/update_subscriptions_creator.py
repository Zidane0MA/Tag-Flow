#!/usr/bin/env python3
"""Actualiza creator_id en subscriptions (id 2..4) a 169 y muestra filas afectadas."""
from pathlib import Path
import sqlite3
import sys


def get_db_path():
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / 'data' / 'videos.db'


def main():
    db = get_db_path()
    if not db.exists():
        print(f"ERROR: No se encuentra la base de datos en {db}")
        sys.exit(2)

    conn = sqlite3.connect(str(db))
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        before = conn.total_changes
        cur = conn.execute("UPDATE subscriptions SET creator_id = 169 WHERE id BETWEEN 2 AND 4")
        conn.commit()
        after = conn.total_changes
        affected = after - before
        print("Consulta ejecutada: UPDATE subscriptions SET creator_id = 169 WHERE id BETWEEN 2 AND 4")
        print(f"Filas afectadas: {affected}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
