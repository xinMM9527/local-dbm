from pydantic import BaseModel
from typing import Optional


class ColumnDef(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    auto_increment: bool = False
    default_value: Optional[str] = None
    comment: Optional[str] = None


class CreateTableRequest(BaseModel):
    conn_id: str
    database: str
    table: str
    columns: list[ColumnDef]
    comment: Optional[str] = None


class AddColumnRequest(BaseModel):
    conn_id: str
    database: str
    table: str
    column: ColumnDef
