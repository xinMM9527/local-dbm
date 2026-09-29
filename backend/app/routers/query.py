from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import time
from datetime import datetime, timezone
from app.config import load_config, save_config
from app.database import get_engine
from app.models.query import QueryRequest

router = APIRouter(prefix="/query", tags=["query"])

MAX_HISTORY = 100


def _get_conn(conn_id: str) -> dict:
    config = load_config()
    conn = next((c for c in config.get("connections", []) if c["id"] == conn_id), None)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn


@router.post("/execute")
async def execute_query(req: QueryRequest):
    conn = _get_conn(req.conn_id)
    engine = await get_engine(conn)

    # Split by semicolons, filter empty
    statements = [s.strip() for s in req.sql.split(";") if s.strip()]
    if not statements:
        raise HTTPException(400, "Empty SQL")

    results = []
    async with engine.connect() as c:
        # Use the specified database if provided
        if req.database and conn["type"] == "mysql":
            await c.execute(text(f"USE `{req.database}`"))
        elif req.database and conn["type"] == "postgresql":
            # PostgreSQL doesn't support USE; connections are per-database
            pass

        for stmt in statements:
            start = time.time()
            try:
                result = await c.execute(text(stmt))
                duration_ms = round((time.time() - start) * 1000, 1)

                if result.returns_rows:
                    columns = list(result.keys())
                    rows = [list(row) for row in result.fetchall()]
                    results.append({
                        "sql": stmt,
                        "columns": columns,
                        "rows": rows,
                        "duration_ms": duration_ms,
                    })
                else:
                    await c.commit()
                    results.append({
                        "sql": stmt,
                        "affected_rows": result.rowcount,
                        "message": "OK",
                        "duration_ms": duration_ms,
                    })
            except Exception as e:
                await c.rollback()
                duration_ms = round((time.time() - start) * 1000, 1)
                results.append({
                    "sql": stmt,
                    "message": f"Error: {str(e)}",
                    "duration_ms": duration_ms,
                })

    # Save to history
    config = load_config()
    history = config.setdefault("query_history", [])
    history.insert(0, {
        "sql": req.sql,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    })
    config["query_history"] = history[:MAX_HISTORY]
    save_config(config)

    return results


@router.get("/history")
async def get_history():
    config = load_config()
    return config.get("query_history", [])


@router.post("/history/clear")
async def clear_history():
    config = load_config()
    config["query_history"] = []
    save_config(config)
    return {"message": "OK"}
