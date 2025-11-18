#!/usr/bin/env python3
"""
Safely delete specified references from subscription_entries in a SQLite DB.
Usage:
  python scripts/delete_subscription_refs.py <path_to_sqlite_db>

What it does:
  - Reports how many of the specified references are present in subscription_entries
  - Deletes those rows inside a transaction and reports deleted count
  - Prints any of the requested URLs that were not present to begin with
"""
import sqlite3
import sys
import os
from datetime import datetime

def process_urls(text):
    """
    Process a string containing URLs with multiple line breaks and return a clean list of URLs.
    
    Args:
        text (str): String containing URLs separated by line breaks
        
    Returns:
        list: List of cleaned URLs
    """
    # Split by any combination of line breaks (\n, \r\n, \r)
    urls = text.splitlines()
    
    # Clean the URLs:
    # 1. Remove leading/trailing whitespace
    # 2. Filter out empty lines
    cleaned_urls = [url.strip() for url in urls if url.strip()]
    
    return cleaned_urls


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/delete_subscription_refs.py <path_to_sqlite_db>')
        sys.exit(2)

    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f'ERROR: Database file not found: {db_path}')
        sys.exit(3)

    print("Pegue las URLs a eliminar (presione Ctrl+Z en Windows o Ctrl+D en Unix y Enter cuando termine):")
    try:
        # Read all input until EOF (Ctrl+Z on Windows, Ctrl+D on Unix)
        urls_input = ""
        while True:
            try:
                line = input()
                urls_input += line + "\n"
            except EOFError:
                break
    
        # Process the URLs
        targets = process_urls(urls_input)
        
        if not targets:
            print("No se proporcionaron URLs válidas.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
    except Exception as e:
        print(f'ERROR: Could not open DB: {e}')
        sys.exit(5)

    try:
        # Find which of the targets exist and count
        placeholders = ','.join('?' for _ in targets) if targets else 'NULL'
        query = f"SELECT reference, COUNT(*) FROM subscription_entries WHERE reference IN ({placeholders}) GROUP BY reference"
        cur.execute(query, targets)
        rows = cur.fetchall()
        present = {r[0]: r[1] for r in rows}

        present_count_total = sum(present.values())
        print(f'Found {len(present)} of {len(targets)} distinct requested URLs present, total matching rows: {present_count_total}')
        if present:
            for ref, cnt in present.items():
                print(f'  {cnt} row(s) with reference: {ref}')

        not_present = [u for u in targets if u not in present]
        if not_present:
            print('\nRequested URLs not present in subscription_entries:')
            for u in not_present:
                print('  ' + u)

        if not present:
            print('\nNo matching rows found; nothing to delete.')
            conn.close()
            sys.exit(0)

        # Delete inside a transaction
        try:
            conn.execute('BEGIN')
            del_query = f"DELETE FROM subscription_entries WHERE reference IN ({placeholders})"
            cur.execute(del_query, targets)
            deleted = cur.rowcount
            conn.commit()
            print(f'\nEliminadas exitosamente {deleted} fila(s).')
        except Exception as e:
            conn.rollback()
            print(f'ERROR durante la eliminación: {e}')
            sys.exit(7)

    except Exception as e:
        print(f'ERROR al consultar la base de datos: {e}')
        sys.exit(6)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
