from pydantic import BaseModel


class ManualBlockRequest(BaseModel):
    registro_id: int
    usuario_id: int
    observaciones: str


class BulkPazSalvoRequest(BaseModel):
    periodo_id: int
    estudiantes_ids: list[int]
    usuario_id: int


class BulkRemoveBlockRequest(BaseModel):
    registro_ids: list[int]
    usuario_id: int
