#!/usr/bin/env python3
"""
Consulta YouTube Data API v3 para obtener publishedAt de un video y lo imprime en formato ISO y segundos Unix.

Uso:
  python scripts/get_youtube_publishedAt.py VIDEO_ID
"""
import sys
import json
import time
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
from config import YOUTUBE_API_KEY

if len(sys.argv) < 2:
    print('USO: get_youtube_publishedAt.py VIDEO_ID')
    sys.exit(1)

video_id = sys.argv[1]
key = YOUTUBE_API_KEY
if not key:
    print('ERROR_NO_API_KEY')
    sys.exit(2)

import urllib.request

url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={key}'
try:
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.load(resp)
except Exception as e:
    print('ERROR_HTTP', e)
    sys.exit(3)

items = data.get('items', [])
if not items:
    print('NOT_FOUND')
    sys.exit(0)

snippet = items[0].get('snippet', {})
publishedAt = snippet.get('publishedAt')
if not publishedAt:
    print('NO_PUBLISHEDAT')
    sys.exit(0)

# publishedAt example: 2020-08-18T20:15:23Z
from datetime import datetime, timezone
try:
    dt = datetime.fromisoformat(publishedAt.replace('Z', '+00:00'))
    unix_ts = int(dt.timestamp())
    print(json.dumps({'video_id': video_id, 'publishedAt': publishedAt, 'unix_ts': unix_ts}, ensure_ascii=False))
    sys.exit(0)
except Exception as e:
    print('PARSE_ERROR', e)
    sys.exit(4)
