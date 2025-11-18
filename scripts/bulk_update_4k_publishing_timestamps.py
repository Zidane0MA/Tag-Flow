#!/usr/bin/env python3
"""
Bulk repair de publishing_timestamp en la BD externa 4K para YouTube.

Comportamiento:
 - Busca registros en `url_description` donde `service_name` es youtube y
   la `media_item_description.publishing_timestamp = -1`.
 - Para cada batch toma las URLs, obtiene video_id, agrupa hasta 50 ids
   por llamada a la YouTube Data API (videos.list) y obtiene publishedAt.
 - Por defecto hace dry-run; use --apply para escribir cambios.
 - Use --one-batch para ejecutar solo un batch y terminar (útil para pruebas).

Uso ejemplo (dry-run primer batch):
  python scripts/bulk_update_4k_publishing_timestamps.py --one-batch

Para aplicar realmente (crea backup):
  python scripts/bulk_update_4k_publishing_timestamps.py --one-batch --apply
"""
import argparse
import sqlite3
import time
import json
import shutil
from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
from config import EXTERNAL_YOUTUBE_DB, YOUTUBE_API_KEY

MAX_IDS_PER_API_CALL = 50


def extract_youtube_id(url: str) -> str:
    import re
    if not url:
        return None
    patterns = [r"v=([A-Za-z0-9_-]{11})", r"youtu\.be/([A-Za-z0-9_-]{11})", r"/shorts/([A-Za-z0-9_-]{11})", r"/embed/([A-Za-z0-9_-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    m = re.search(r"([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def query_pending_rows(external_db: Path, limit: int, offset: int):
    conn = sqlite3.connect(str(external_db))
    try:
        q = '''SELECT DISTINCT ud.media_item_description_id, ud.url
               FROM url_description ud
               JOIN media_item_description mid ON ud.media_item_description_id = mid.id
               WHERE lower(ud.service_name) LIKE 'youtube%'
                 AND mid.publishing_timestamp = -1
               ORDER BY ud.media_item_description_id
               LIMIT ? OFFSET ?'''
        cur = conn.execute(q, (limit, offset))
        return cur.fetchall()
    finally:
        conn.close()


def fetch_publishedAt_for_ids(video_ids, throttle_ms=200, max_retries=3):
    # returns dict video_id -> unix_ts or None
    import urllib.request
    from datetime import datetime
    out = {}
    # process in chunks of MAX_IDS_PER_API_CALL
    ids = list(video_ids)
    for i in range(0, len(ids), MAX_IDS_PER_API_CALL):
        chunk = ids[i:i+MAX_IDS_PER_API_CALL]
        qids = ','.join(chunk)
        url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={qids}&key={YOUTUBE_API_KEY}'
        attempt = 0
        while attempt <= max_retries:
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    data = json.load(resp)
                items = data.get('items', [])
                found = {it['id']: it.get('snippet', {}).get('publishedAt') for it in items}
                for vid in chunk:
                    publishedAt = found.get(vid)
                    if publishedAt:
                        dt = datetime.fromisoformat(publishedAt.replace('Z', '+00:00'))
                        out[vid] = int(dt.timestamp())
                    else:
                        out[vid] = None
                break
            except Exception as e:
                attempt += 1
                wait = (2 ** attempt)
                print(f'Warning: API call failed (attempt {attempt}) error={e}; sleeping {wait}s')
                time.sleep(wait)
        # throttle between API calls
        time.sleep(throttle_ms / 1000.0)
    return out


def retry_missing_ids(missing_vids, throttle_ms=500, extra_retries=3):
    """Retry each missing video id individually with extra retries and longer throttle.
    Returns dict vid->unix_ts (only for those found).
    """
    results = {}
    for vid in missing_vids:
        # try individual request with retries
        got = None
        for attempt in range(1, extra_retries + 1):
            try:
                import urllib.request
                from datetime import datetime
                url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}&key={YOUTUBE_API_KEY}'
                with urllib.request.urlopen(url, timeout=15) as resp:
                    data = json.load(resp)
                items = data.get('items', [])
                if items:
                    publishedAt = items[0].get('snippet', {}).get('publishedAt')
                    if publishedAt:
                        dt = datetime.fromisoformat(publishedAt.replace('Z', '+00:00'))
                        got = int(dt.timestamp())
                        break
            except Exception as e:
                wait = 2 ** attempt
                print(f'  retry_missing_ids: attempt {attempt} for {vid} failed: {e}; sleep {wait}s')
                time.sleep(wait)
        if got:
            results[vid] = got
        time.sleep(throttle_ms / 1000.0)
    return results


def apply_updates(external_db: Path, updates: dict):
    # updates: {media_item_description_id: unix_ts}
    conn = sqlite3.connect(str(external_db))
    try:
        updated = 0
        with conn:
            for mid, ts in updates.items():
                cur = conn.execute('UPDATE media_item_description SET publishing_timestamp=? WHERE id=? AND (publishing_timestamp = -1 OR publishing_timestamp <= 0 OR publishing_timestamp IS NULL)', (ts, mid))
                updated += cur.rowcount
        return updated
    finally:
        conn.close()


def count_pending(external_db: Path):
    conn = sqlite3.connect(str(external_db))
    try:
        q = '''SELECT COUNT(DISTINCT ud.media_item_description_id)
               FROM url_description ud
               JOIN media_item_description mid ON ud.media_item_description_id = mid.id
               WHERE lower(ud.service_name) LIKE 'youtube%'
                 AND mid.publishing_timestamp = -1'''
        cur = conn.execute(q)
        return cur.fetchone()[0]
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--external-db', help='Ruta a la BD externa (opcional)')
    parser.add_argument('--batch-size', type=int, default=200, help='Número de media_item ids por batch (default 200)')
    parser.add_argument('--throttle-ms', type=int, default=200, help='Milisegundos a esperar entre llamadas API (default 200ms)')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (por defecto dry-run)')
    parser.add_argument('--one-batch', action='store_true', help='Procesar solo un batch y salir')
    parser.add_argument('--offset', type=int, default=0, help='Offset inicial (para reanudar)')
    args = parser.parse_args()

    external_db = Path(args.external_db) if args.external_db else EXTERNAL_YOUTUBE_DB
    if not external_db or not external_db.exists():
        print('ERROR: external DB not found:', external_db)
        sys.exit(2)
    if not YOUTUBE_API_KEY:
        print('ERROR: YOUTUBE_API_KEY not configured')
        sys.exit(2)

    pending_total = count_pending(external_db)
    print(f'Pending media_item_description ids with publishing_timestamp=-1 and service_name youtube: {pending_total}')

    offset = args.offset
    batch_num = 0
    overall_updates = 0

    while True:
        batch_num += 1
        rows = query_pending_rows(external_db, args.batch_size, offset)
        if not rows:
            print('No more rows to process. Exiting.')
            break
        print(f'Processing batch #{batch_num} (offset={offset}) rows_found={len(rows)})')
        # rows: list of (mid_id, url)
        mid_to_url = {r[0]: r[1] for r in rows}
        video_ids = {}
        for mid, url in mid_to_url.items():
            vid = extract_youtube_id(url)
            if vid:
                video_ids[mid] = vid
            else:
                print(f'Warning: no video_id extracted for media_item_description_id={mid} url={url}')

        if not video_ids:
            print('No valid video ids in this batch. Advancing.')
            offset += args.batch_size
            if args.one_batch:
                break
            continue

        unique_vids = list({v for v in video_ids.values()})
        print(f'Unique video ids to query: {len(unique_vids)}')

        vid_to_ts = fetch_publishedAt_for_ids(unique_vids, throttle_ms=args.throttle_ms)

        # If some vids returned None, attempt individual retries with a longer throttle
        missing_vids = [v for v, t in vid_to_ts.items() if t is None]
        if missing_vids:
            print(f'{len(missing_vids)} video ids had no publishedAt in batch; retrying individually...')
            extra = retry_missing_ids(missing_vids, throttle_ms=max(300, args.throttle_ms), extra_retries=3)
            # merge extra results into vid_to_ts
            for k, v in extra.items():
                vid_to_ts[k] = v

        # prepare updates for mids where we have a ts
        updates = {}
        for mid, vid in video_ids.items():
            ts = vid_to_ts.get(vid)
            if ts:
                updates[mid] = ts

        if not updates:
            print('No updates found for this batch (API returned no dates).')
        else:
            print('The following updates would be applied:')
            for mid, ts in updates.items():
                print(f'  mid={mid} -> {ts} ({time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))})')

            if args.apply:
                # backup external DB once before first apply
                if overall_updates == 0:
                    bakdir = Path('backups')
                    bakdir.mkdir(parents=True, exist_ok=True)
                    bak = bakdir / f'external_bulk_preapply_{time.strftime("%Y%m%d_%H%M%S")}.sqlite'
                    shutil.copy2(external_db, bak)
                    print('Backup created at', bak)
                updated = apply_updates(external_db, updates)
                overall_updates += updated
                print(f'Applied updates to external DB: {updated} rows in this batch')
            else:
                print('Dry-run: no database changes performed. Use --apply to write.')

        # advance offset / exit if one-batch
        offset += args.batch_size
        if args.one_batch:
            print('one-batch flag set: exiting after first batch')
            break

    print('Done. Total applied updates:', overall_updates)


if __name__ == '__main__':
    main()
