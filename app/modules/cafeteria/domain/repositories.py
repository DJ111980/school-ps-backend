"""
Cafeteria Module Domain Repository Interface.

Author: Danilo Castillejo
Role: Developer of the cafeteria module
"""

from abc import ABC, abstractmethod
from app.modules.auth.infrastructure.models import Usuario
from app.modules.enrollment.infrastructure.models import Estudiante, Periodo, Grado
from app.modules.cafeteria.infrastructure.models import Cafeteria


class CafeteriaRepositoryInterface(ABC):
    """
    Abstract interface that defines the data access rules.
    This allows the Domain Service to be independent of the specific ORM or Database.
    """

    @abstractmethod
    async def get_all_by_period(
        self, periodo_id: int
    ) -> list[tuple[Cafeteria, Estudiante]]:
        pass

    @abstractmethod
    async def get_by_id(self, registro_id: int) -> Cafeteria | None:
        pass

    @abstractmethod
    async def get_by_student_and_period(
        self, estudiante_id: int, periodo_id: int
    ) -> Cafeteria | None:
        pass

    @abstractmethod
    async def save(self, record: Cafeteria) -> Cafeteria:
        pass

    @abstractmethod
    async def get_active_students(self) -> list[Estudiante]:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Usuario | None:
        pass

    @abstractmethod
    async def get_period_by_id(self, periodo_id: int) -> Periodo | None:
        pass

    @abstractmethod
    async def get_report_data(
        self, periodo_id: int
    ) -> list[tuple[Cafeteria, Estudiante, Grado]]:
        """Contract to fetch data for the CSV report."""
        pass
