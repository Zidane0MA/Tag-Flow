#!/usr/bin/env python3
"""
Check last 5000 URLs from subscription_entries.reference against url_description.url
Print any missing URLs (one per line).
Usage: python scripts/check_missing_urls_db.py <path_to_sqlite_db>
"""
import sqlite3
import sys
import os


def find_last_5000_references(cur):
    # Try several timestamp-like columns for ordering, else fallback to ROWID
    candidates = [
        'created_at', 'created', 'inserted_at', 'timestamp', 'updated_at', 'updated'
    ]
    for col in candidates:
        try:
            cur.execute(f"SELECT reference FROM subscription_entries WHERE reference IS NOT NULL ORDER BY {col} DESC LIMIT 5000")
            rows = [r[0] for r in cur.fetchall()]
            if rows:
                return rows
        except sqlite3.OperationalError:
            # Column doesn't exist or query failed; try next
            continue
    # Fallback to ROWID ordering
    cur.execute("SELECT reference FROM subscription_entries WHERE reference IS NOT NULL ORDER BY ROWID DESC LIMIT 5000")
    return [r[0] for r in cur.fetchall()]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_missing_urls_db.py <path_to_sqlite_db>")
        sys.exit(2)

    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        sys.exit(3)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
    except Exception as e:
        print(f"ERROR: Could not open DB: {e}")
        sys.exit(4)

    try:
        refs = find_last_5000_references(cur)
    except Exception as e:
        print(f"ERROR while querying subscription_entries: {e}")
        conn.close()
        sys.exit(5)

    if not refs:
        print("No references found in subscription_entries (or table empty).")
        conn.close()
        sys.exit(0)

    # Deduplicate while preserving order
    seen = set()
    refs_unique = []
    for r in refs:
        if r is None:
            continue
        if r in seen:
            continue
        seen.add(r)
        refs_unique.append(r)

    missing = []
    try:
        for ref in refs_unique:
            cur.execute("SELECT 1 FROM url_description WHERE url = ? LIMIT 1", (ref,))
            if cur.fetchone() is None:
                missing.append(ref)
    except Exception as e:
        print(f"ERROR while checking url_description: {e}")
        conn.close()
        sys.exit(6)

    conn.close()

    if missing:
        print(f"Missing {len(missing)} URLs out of {len(refs_unique)} (last {len(refs)} entries taken, {len(refs_unique)} unique):")
        for u in missing:
            print(u)
        # Exit code 1 to indicate missing items found
        sys.exit(1)
    else:
        print(f"All {len(refs_unique)} URLs were found in url_description.")
        sys.exit(0)


if __name__ == '__main__':
    main()
