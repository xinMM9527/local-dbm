from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    conn_id: str
    sql: str
    database: Optional[str] = None
