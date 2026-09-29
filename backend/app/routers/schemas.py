from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.config import load_config
from app.database import get_engine

router = APIRouter(prefix="/schemas", tags=["schemas"])


def _get_conn(conn_id: str) -> dict:
    config = load_config()
    conn = next((c for c in config.get("connections", []) if c["id"] == conn_id), None)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn


@router.get("/databases")
async def list_databases(conn_id: str = Query(...)):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)
    async with engine.connect() as c:
        if conn["type"] == "mysql":
            result = await c.execute(text("SHOW DATABASES"))
            rows = [r[0] for r in result.fetchall()]
            # Filter out system databases
            exclude = {"information_schema", "performance_schema", "mysql", "sys"}
            return [r for r in rows if r not in exclude]
        elif conn["type"] == "postgresql":
            result = await c.execute(text(
                "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
            ))
            return [r[0] for r in result.fetchall()]
    return []


@router.get("/tables")
async def list_tables(conn_id: str = Query(...), database: str = Query(...)):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)
    async with engine.connect() as c:
        if conn["type"] == "mysql":
            result = await c.execute(text(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            ), {"db": database})
        elif conn["type"] == "postgresql":
            result = await c.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
        else:
            return []
        return [r[0] for r in result.fetchall()]


@router.get("/columns")
async def list_columns(
    conn_id: str = Query(...),
    database: str = Query(...),
    table: str = Query(...),
):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)
    async with engine.connect() as c:
        if conn["type"] == "mysql":
            result = await c.execute(text("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                       COLUMN_COMMENT, COLUMN_KEY, EXTRA
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl
                ORDER BY ORDINAL_POSITION
            """), {"db": database, "tbl": table})
            columns = []
            for row in result.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default_value": row[3],
                    "comment": row[4] or None,
                    "is_primary_key": row[5] == "PRI",
                    "is_auto_increment": "auto_increment" in (row[6] or ""),
                })
            return columns

        elif conn["type"] == "postgresql":
            result = await c.execute(text("""
                SELECT c.column_name, c.data_type, c.is_nullable, c.column_default,
                       CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = :tbl AND tc.constraint_type = 'PRIMARY KEY'
                ) pk ON pk.column_name = c.column_name
                WHERE c.table_schema = 'public' AND c.table_name = :tbl
                ORDER BY c.ordinal_position
            """), {"tbl": table})
            columns = []
            for row in result.fetchall():
                default_val = row[3]
                is_auto = False
                if default_val and "nextval" in str(default_val):
                    is_auto = True
                    default_val = None
                columns.append({
                    "name": row[0],
                    "type": row[1].upper(),
                    "nullable": row[2] == "YES",
                    "default_value": default_val,
                    "comment": None,
                    "is_primary_key": row[4],
                    "is_auto_increment": is_auto,
                })
            return columns
    return []


@router.get("/indexes")
async def list_indexes(
    conn_id: str = Query(...),
    database: str = Query(...),
    table: str = Query(...),
):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)
    async with engine.connect() as c:
        if conn["type"] == "mysql":
            result = await c.execute(text(
                "SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE "
                "FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl "
                "ORDER BY INDEX_NAME, SEQ_IN_INDEX"
            ), {"db": database, "tbl": table})
            indexes: dict[str, dict] = {}
            for row in result.fetchall():
                name = row[0]
                if name not in indexes:
                    indexes[name] = {"name": name, "columns": [], "unique": row[2] == 0}
                indexes[name]["columns"].append(row[1])
            return list(indexes.values())

        elif conn["type"] == "postgresql":
            result = await c.execute(text("""
                SELECT i.relname as index_name, ix.indisunique,
                       array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns
                FROM pg_index ix
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = :tbl AND NOT ix.indisprimary
                GROUP BY i.relname, ix.indisunique
            """), {"tbl": table})
            return [
                {"name": row[0], "columns": row[2], "unique": row[1]}
                for row in result.fetchall()
            ]
    return []
