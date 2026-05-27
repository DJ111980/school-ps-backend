"""
Cafeteria Module Infrastructure Repository.

Author: Danilo Castillejo
Role: Developer of the cafeteria module
"""

from sqlmodel import select, col
from app.core.db import SessionDep
from app.modules.auth.infrastructure.models import Usuario
from app.modules.enrollment.infrastructure.models import Estudiante, Periodo, Grado
from app.modules.cafeteria.infrastructure.models import Cafeteria
from app.modules.cafeteria.domain.repositories import CafeteriaRepositoryInterface


class CafeteriaRepository(CafeteriaRepositoryInterface):
    def __init__(self, session: SessionDep):
        self.session = session

    async def get_all_by_period(
        self, periodo_id: int
    ) -> list[tuple[Cafeteria, Estudiante]]:
        """
        Retrieves cafeteria records joined with Student data.
        We use a JOIN here to avoid the 'N+1' problem (multiple queries for names).
        """
        statement = (
            select(Cafeteria, Estudiante)
            .join(Estudiante, col(Cafeteria.estudiante_id) == col(Estudiante.id))
            .where(Cafeteria.periodo_id == periodo_id)
        )
        results = self.session.execute(statement).all()
        # Returns a list of tuples (Cafeteria, Estudiante)
        return [(r[0], r[1]) for r in results]

    async def get_by_id(self, registro_id: int) -> Cafeteria | None:
        return self.session.get(Cafeteria, registro_id)

    async def get_by_student_and_period(
        self, estudiante_id: int, periodo_id: int
    ) -> Cafeteria | None:
        statement = select(Cafeteria).where(
            Cafeteria.estudiante_id == estudiante_id, Cafeteria.periodo_id == periodo_id
        )
        return self.session.exec(statement).first()

    async def save(self, record: Cafeteria) -> Cafeteria:
        """Handles both creation and updates (Upsert logic)."""
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    async def get_active_students(self) -> list[Estudiante]:
        return list(
            self.session.exec(select(Estudiante).where(Estudiante.activo)).all()
        )

    async def get_user_by_id(self, user_id: int) -> Usuario | None:
        return self.session.get(Usuario, user_id)

    async def get_period_by_id(self, periodo_id: int) -> Periodo | None:
        return self.session.get(Periodo, periodo_id)

    async def get_report_data(
        self, periodo_id: int
    ) -> list[tuple[Cafeteria, Estudiante, Grado]]:
        """
        CAF-RF-12: Fetches cafeteria records joined with Student and Grade
        to provide human-readable reports.
        """
        statement = (
            select(Cafeteria, Estudiante, Grado)
            .join(Estudiante, col(Cafeteria.estudiante_id) == col(Estudiante.id))
            .join(Grado, col(Estudiante.grado_id) == col(Grado.id))
            .where(Cafeteria.periodo_id == periodo_id)
        )
        results = self.session.execute(statement).all()

        # SQLModel returns rows as tuples, we cast them for type safety
        return [(r[0], r[1], r[2]) for r in results]
