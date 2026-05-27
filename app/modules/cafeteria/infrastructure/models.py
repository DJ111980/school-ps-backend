from typing import Optional
from sqlmodel import Field, UniqueConstraint
from app.shared.infrastructure.base import Base


class Cafeteria(Base, table=True):
    __table_args__ = (
        UniqueConstraint(
            "estudiante_id", "periodo_id", name="unique_student_period_cafeteria"
        ),
    )

    estudiante_id: int = Field(foreign_key="estudiante.id")
    periodo_id: int = Field(foreign_key="periodo.id")
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    # True = PAZ Y SALVO / False = NO PAZ Y SALVO (Bloqueado)
    estado_cafeteria: bool = Field(default=True)

    # CAF-RF-03: Obligatoria cuando estado_cafeteria es False
    observaciones: Optional[str] = Field(default=None, max_length=400)

    @property
    def firmado(self) -> bool:
        return self.estado_cafeteria
