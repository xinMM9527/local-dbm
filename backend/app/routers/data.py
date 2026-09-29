from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
import json
import csv
import io
from app.config import load_config
from app.database import get_engine

router = APIRouter(prefix="/data", tags=["data"])


def _get_conn(conn_id: str) -> dict:
    config = load_config()
    conn = next((c for c in config.get("connections", []) if c["id"] == conn_id), None)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn


@router.get("/{database}/{table}")
async def query_data(
    database: str,
    table: str,
    conn_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)
    offset = (page - 1) * size

    async with engine.connect() as c:
        db_type = conn["type"]
        if db_type == "mysql":
            await c.execute(text(f"USE `{database}`"))
            count_result = await c.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
            total = count_result.scalar()
            result = await c.execute(text(f"SELECT * FROM `{table}` LIMIT :limit OFFSET :offset"),
                                     {"limit": size, "offset": offset})
        elif db_type == "postgresql":
            count_result = await c.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            total = count_result.scalar()
            result = await c.execute(text(f'SELECT * FROM "{table}" LIMIT :limit OFFSET :offset'),
                                     {"limit": size, "offset": offset})
        else:
            raise HTTPException(400, "Unsupported db type")

        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]

    return {"columns": columns, "rows": rows, "total": total}


@router.post("/{database}/{table}")
async def insert_row(database: str, table: str, body: dict):
    conn = _get_conn(body["conn_id"])
    engine = await get_engine(conn)
    row = body["row"]

    cols = list(row.keys())
    vals = list(row.values())
    placeholders = ", ".join([f":v{i}" for i in range(len(vals))])
    params = {f"v{i}": v for i, v in enumerate(vals)}

    db_type = conn["type"]
    if db_type == "mysql":
        col_str = ", ".join([f"`{c}`" for c in cols])
        sql = f"INSERT INTO `{table}` ({col_str}) VALUES ({placeholders})"
    else:
        col_str = ", ".join([f'"{c}"' for c in cols])
        sql = f'INSERT INTO "{table}" ({col_str}) VALUES ({placeholders})'

    async with engine.begin() as c:
        if db_type == "mysql":
            await c.execute(text(f"USE `{database}`"))
        result = await c.execute(text(sql), params)

    return {"affected_rows": result.rowcount, "message": "OK"}


@router.put("/{database}/{table}")
async def update_row(database: str, table: str, body: dict):
    conn = _get_conn(body["conn_id"])
    engine = await get_engine(conn)
    row = body["row"]

    # Assume 'id' is the primary key for simplicity
    pk_col = "id"
    if pk_col not in row:
        raise HTTPException(400, "Row must contain 'id' field as primary key")

    pk_val = row.pop(pk_col)
    set_parts = []
    params = {"pk": pk_val}
    for i, (k, v) in enumerate(row.items()):
        set_parts.append(f"`{k}` = :v{i}" if conn["type"] == "mysql" else f'"{k}" = :v{i}')
        params[f"v{i}"] = v

    db_type = conn["type"]
    tbl = f"`{table}`" if db_type == "mysql" else f'"{table}"'
    pk_ref = f"`{pk_col}`" if db_type == "mysql" else f'"{pk_col}"'
    sql = f"UPDATE {tbl} SET {', '.join(set_parts)} WHERE {pk_ref} = :pk"

    async with engine.begin() as c:
        if db_type == "mysql":
            await c.execute(text(f"USE `{database}`"))
        result = await c.execute(text(sql), params)

    return {"affected_rows": result.rowcount, "message": "OK"}


@router.delete("/{database}/{table}")
async def delete_row(database: str, table: str, body: dict):
    conn = _get_conn(body["conn_id"])
    engine = await get_engine(conn)
    conditions = body["conditions"]

    where_parts = []
    params = {}
    db_type = conn["type"]
    for i, (k, v) in enumerate(conditions.items()):
        col_ref = f"`{k}`" if db_type == "mysql" else f'"{k}"'
        where_parts.append(f"{col_ref} = :c{i}")
        params[f"c{i}"] = v

    tbl = f"`{table}`" if db_type == "mysql" else f'"{table}"'
    sql = f"DELETE FROM {tbl} WHERE {' AND '.join(where_parts)}"

    async with engine.begin() as c:
        if db_type == "mysql":
            await c.execute(text(f"USE `{database}`"))
        result = await c.execute(text(sql), params)

    return {"affected_rows": result.rowcount, "message": "OK"}


@router.get("/{database}/{table}/export")
async def export_data(
    database: str,
    table: str,
    conn_id: str = Query(...),
    format: str = Query("csv"),
):
    conn = _get_conn(conn_id)
    engine = await get_engine(conn)

    async with engine.connect() as c:
        db_type = conn["type"]
        if db_type == "mysql":
            await c.execute(text(f"USE `{database}`"))
            result = await c.execute(text(f"SELECT * FROM `{table}`"))
        else:
            result = await c.execute(text(f'SELECT * FROM "{table}"'))

        columns = list(result.keys())
        rows = result.fetchall()

    if format == "json":
        data = [dict(zip(columns, row)) for row in rows]
        content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        media_type = "application/json"
        filename = f"{table}.json"
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"{table}.csv"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
