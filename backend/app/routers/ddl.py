from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.config import load_config
from app.database import get_engine
from app.models.ddl import CreateTableRequest, AddColumnRequest

router = APIRouter(prefix="/ddl", tags=["ddl"])


def _get_conn(conn_id: str) -> dict:
    config = load_config()
    conn = next((c for c in config.get("connections", []) if c["id"] == conn_id), None)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn


def _build_column_sql(col, db_type: str) -> str:
    parts = [f"`{col.name}`" if db_type == "mysql" else f'"{col.name}"', col.type]

    if col.primary_key:
        parts.append("PRIMARY KEY")
    if col.auto_increment:
        if db_type == "mysql":
            parts.append("AUTO_INCREMENT")
        elif db_type == "postgresql":
            # Replace INT/BIGINT with SERIAL/BIGSERIAL
            upper = col.type.upper()
            if "BIGINT" in upper:
                parts[1] = "BIGSERIAL"
            else:
                parts[1] = "SERIAL"
            # Remove PRIMARY KEY duplicate if already added
            pass

    if not col.nullable and not col.auto_increment:
        parts.append("NOT NULL")
    elif col.nullable and not col.primary_key:
        parts.append("NULL")

    if col.default_value is not None and not col.auto_increment:
        parts.append(f"DEFAULT {col.default_value}")

    if col.comment and db_type == "mysql":
        parts.append(f"COMMENT '{col.comment}'")

    return " ".join(parts)


@router.post("/create-table")
async def create_table(req: CreateTableRequest):
    conn = _get_conn(req.conn_id)
    engine = await get_engine(conn)
    db_type = conn["type"]

    col_defs = [_build_column_sql(c, db_type) for c in req.columns]
    cols_sql = ",\n  ".join(col_defs)

    if db_type == "mysql":
        table_name = f"`{req.table}`"
        comment_sql = f" COMMENT='{req.comment}'" if req.comment else ""
        sql = f"CREATE TABLE {table_name} (\n  {cols_sql}\n){comment_sql}"
    elif db_type == "postgresql":
        table_name = f'"{req.table}"'
        sql = f'CREATE TABLE {table_name} (\n  {cols_sql}\n)'
        if req.comment:
            sql += f';\nCOMMENT ON TABLE {table_name} IS \'{req.comment}\''
    else:
        raise HTTPException(400, f"Unsupported db type: {db_type}")

    async with engine.begin() as c:
        if db_type == "mysql" and req.database:
            await c.execute(text(f"USE `{req.database}`"))
        # Execute each statement separately for PG (may have multiple statements)
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                await c.execute(text(stmt))

    return {"message": "OK", "sql": sql}


@router.post("/add-column")
async def add_column(req: AddColumnRequest):
    conn = _get_conn(req.conn_id)
    engine = await get_engine(conn)
    db_type = conn["type"]

    col = req.column
    if db_type == "mysql":
        col_sql = _build_column_sql(col, db_type)
        sql = f"ALTER TABLE `{req.table}` ADD COLUMN {col_sql}"
    elif db_type == "postgresql":
        parts = [f'"{col.name}"', col.type]
        if not col.nullable:
            parts.append("NOT NULL")
        if col.default_value is not None:
            parts.append(f"DEFAULT {col.default_value}")
        col_def = " ".join(parts)
        sql = f'ALTER TABLE "{req.table}" ADD COLUMN {col_def}'
    else:
        raise HTTPException(400, f"Unsupported db type: {db_type}")

    async with engine.begin() as c:
        if db_type == "mysql" and req.database:
            await c.execute(text(f"USE `{req.database}`"))
        await c.execute(text(sql))

    return {"message": "OK", "sql": sql}
