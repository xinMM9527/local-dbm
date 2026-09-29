from fastapi import APIRouter, HTTPException
from app.config import load_config, save_config, generate_id
from app.database import test_connection, dispose_engine
from app.models.connection import ConnectionCreate, ConnectionUpdate, ConnectionResponse

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionResponse])
async def list_connections():
    config = load_config()
    return config.get("connections", [])


@router.post("", response_model=ConnectionResponse)
async def create_connection(body: ConnectionCreate):
    config = load_config()
    conn = {"id": generate_id(), **body.model_dump()}
    config.setdefault("connections", []).append(conn)
    save_config(config)
    return conn


@router.put("/{conn_id}", response_model=ConnectionResponse)
async def update_connection(conn_id: str, body: ConnectionUpdate):
    config = load_config()
    conns = config.get("connections", [])
    for i, c in enumerate(conns):
        if c["id"] == conn_id:
            await dispose_engine(conn_id)
            conns[i] = {"id": conn_id, **body.model_dump()}
            save_config(config)
            return conns[i]
    raise HTTPException(404, "Connection not found")


@router.delete("/{conn_id}")
async def delete_connection(conn_id: str):
    config = load_config()
    conns = config.get("connections", [])
    new_conns = [c for c in conns if c["id"] != conn_id]
    if len(new_conns) == len(conns):
        raise HTTPException(404, "Connection not found")
    await dispose_engine(conn_id)
    config["connections"] = new_conns
    save_config(config)
    return {"message": "OK"}


@router.post("/{conn_id}/test")
async def test_conn(conn_id: str):
    config = load_config()
    conn = next((c for c in config.get("connections", []) if c["id"] == conn_id), None)
    if not conn:
        raise HTTPException(404, "Connection not found")
    try:
        await test_connection(conn)
        return {"message": "Connection successful"}
    except Exception as e:
        raise HTTPException(400, f"Connection failed: {str(e)}")
