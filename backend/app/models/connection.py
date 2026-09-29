from pydantic import BaseModel
from typing import Optional


class ConnectionCreate(BaseModel):
    name: str
    type: str  # mysql | postgresql
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = "root"
    password: str = ""
    database: str = ""


class ConnectionUpdate(ConnectionCreate):
    pass


class ConnectionResponse(ConnectionCreate):
    id: str
