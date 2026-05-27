from typing import List
from pydantic import BaseModel


# CAF-RF-02, 03: Para el bloqueo manual
class ManualBlockSchema(BaseModel):
    registro_id: int
    usuario_id: int
    observaciones: str  # Obligatoria según SRS


# CAF-RF-05: Para la asignación masiva
class BulkPazSalvoSchema(BaseModel):
    periodo_id: int
    estudiantes_ids: List[int]  # Todos los seleccionados en la interfaz
    usuario_id: int


class BulkRemoveBlockSchema(BaseModel):
    registro_ids: List[int]  # IDs de la tabla cafeteria que quieres poner al día
    usuario_id: int
