#!/usr/bin/env python3
"""Ejecuta las tres consultas solicitadas sobre la BD local `data/videos.db`.

1) UPDATE posts -> set creator_id = NULL where platform_id=4 and creator name = 'undefined'
2) DELETE FROM creators where name = 'undefined'
3) UPDATE posts -> set creator_id = 169 where platform_id=4

Imprime filas afectadas por cada consulta.
"""
from pathlib import Path
import sqlite3
import sys


def get_db_path():
    # scripts/.. -> repo root
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / 'data' / 'videos.db'


def run_queries(db_path: Path):
    if not db_path.exists():
        print(f"ERROR: base de datos no encontrada en: {db_path}")
        sys.exit(2)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute('PRAGMA foreign_keys = ON')

        def run(sql, params=None):
            before = conn.total_changes
            cur = conn.execute(sql) if not params else conn.execute(sql, params)
            conn.commit()
            after = conn.total_changes
            affected = after - before
            print("---")
            print(f"Consulta ejecutada:\n{sql}")
            print(f"Filas afectadas: {affected}")
            return affected

        # 1) Establecer NULL en posts cuyo creator corresponde a creators.name='undefined' y platform_id=4
        q1 = (
            "UPDATE posts SET creator_id = NULL "
            "WHERE platform_id = 4 AND creator_id IN (SELECT id FROM creators WHERE name = 'undefined')"
        )

        # 2) Borrar creadores con name = 'undefined'
        q2 = "DELETE FROM creators WHERE name = 'undefined'"

        # 3) Actualizar posts de platform_id=4 para asignar creator_id=169
        q3 = "UPDATE posts SET creator_id = 169 WHERE platform_id = 4"

        run(q1)
        run(q2)
        run(q3)

    finally:
        conn.close()


if __name__ == '__main__':
    dbp = get_db_path()
    print(f"Usando base de datos: {dbp}")
    run_queries(dbp)
