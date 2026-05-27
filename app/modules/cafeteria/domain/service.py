"""
Cafeteria Module Domain Service.

This service implements the core business rules:
1. Automatic synchronization of active students.
2. Manual blocking (marking debt) with mandatory comments.
3. Bulk update that protects manually blocked records.

Author: Danilo Castillejo
Role: Developer of the cafeteria module
"""

from datetime import datetime
from app.modules.cafeteria.domain.repositories import CafeteriaRepositoryInterface
from app.modules.cafeteria.infrastructure.models import Cafeteria


class CafeteriaService:
    def __init__(self, repository: CafeteriaRepositoryInterface):
        self.repository = repository

    async def sync_students(self, periodo_id: int) -> None:
        """
        Ensures the cafeteria table is populated with all active students.
        If a student is active but has no record for the period, one is created.
        """
        students = await self.repository.get_active_students()
        for student in students:
            if student.id is None:
                continue
            exists = await self.repository.get_by_student_and_period(
                student.id, periodo_id
            )
            if not exists:
                new_record = Cafeteria(
                    estudiante_id=student.id,
                    periodo_id=periodo_id,
                    estado_cafeteria=True,  # Default to Paz y Salvo
                )
                await self.repository.save(new_record)

    async def get_status_list(self, periodo_id: int) -> list[dict]:
        """Returns a formatted list of students and their cafeteria status."""
        await self.sync_students(periodo_id)
        results = await self.repository.get_all_by_period(periodo_id)

        # Formatting the response into a simple dictionary list for the frontend
        return [
            {
                "id": c.id,
                "estudiante": e.nombre,
                "documento": e.documento,
                "estado": c.estado_cafeteria,
                "observaciones": c.observaciones,
            }
            for c, e in results
        ]

    async def create_manual_block(self, registro_id: int, usuario_id: int, obs: str):
        """
        Marks a student as 'No Paz y Salvo' manually.
        Validation: Observations are mandatory for manual blocks.
        """
        if not obs or len(obs.strip()) < 5:
            raise ValueError("A valid observation is mandatory for manual blocks.")

        user = await self.repository.get_user_by_id(usuario_id)
        if not user:
            raise ValueError("Responsible user not found.")

        record = await self.repository.get_by_id(registro_id)
        if not record:
            raise ValueError("Cafeteria record not found.")

        record.estado_cafeteria = False  # Blocked
        record.observaciones = obs
        record.usuario_id = usuario_id
        record.updated_at = datetime.now()
        return await self.repository.save(record)

    async def bulk_update_paz_y_salvo(
        self, periodo_id: int, estudiantes_ids: list[int], usuario_id: int
    ) -> dict:
        """
        The 'Select All' logic.
        CRITICAL RULE: If a student is already marked as False (Debt),
        the bulk operation MUST NOT overwrite it.
        """
        actualizados, excluidos = 0, 0
        for est_id in estudiantes_ids:
            record = await self.repository.get_by_student_and_period(est_id, periodo_id)

            # If record exists and is already False (Manual Block), we skip it.
            if record and not record.estado_cafeteria:
                excluidos += 1
            elif record:
                # Only update those who are currently True or new.
                record.estado_cafeteria = True
                record.usuario_id = usuario_id
                await self.repository.save(record)
                actualizados += 1

        return {
            "total_seleccionados": len(estudiantes_ids),
            "total_actualizados": actualizados,
            "total_excluidos": excluidos,
        }

    async def bulk_remove_manual_blocks(
        self, usuario_id: int, registro_ids: list[int]
    ) -> int:
        """CAF-RF-09: Removes manual blocks for multiple records."""
        count = 0
        for rid in registro_ids:
            record = await self.repository.get_by_id(rid)
            if record:
                record.estado_cafeteria = True
                record.usuario_id = usuario_id
                record.observaciones = "Bloqueo retirado manualmente"
                await self.repository.save(record)
                count += 1
        return count
