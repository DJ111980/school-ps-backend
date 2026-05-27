"""
Cafeteria Module Get Individual Student Status Use Case.

Author: Danilo Castillejo
Role: Developer of the cafeteria module
"""

from app.core.db import SessionDep
from app.modules.cafeteria.infrastructure.repository import CafeteriaRepository


class GetStudentStatus:
    """Use case for an individual student to check their own cafeteria status."""

    def __init__(self, session: SessionDep):
        self.repository = CafeteriaRepository(session=session)

    async def execute(self, estudiante_id: int, periodo_id: int):
        return await self.repository.get_by_student_and_period(
            estudiante_id, periodo_id
        )
