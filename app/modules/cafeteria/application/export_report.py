"""
Cafeteria Module Export Report Use Case.

Author: Danilo Castillejo
Role: Developer of the cafeteria module
"""

import csv
import io
from app.core.db import SessionDep
from app.modules.cafeteria.infrastructure.repository import CafeteriaRepository


class ExportReport:
    """
    Use case to generate a CSV report for cafeteria status.
    It fetches data from the repository and formats it as a CSV string.
    """

    def __init__(self, session: SessionDep):
        self.repository = CafeteriaRepository(session=session)

    async def execute(self, periodo_id: int) -> str:
        # Fetch data using the repository (No SQL logic here)
        results = await self.repository.get_report_data(periodo_id)

        # Create an in-memory string buffer for the CSV
        output = io.StringIO()  # type: ignore[abstract]
        writer = csv.writer(output)

        # Header row
        writer.writerow(["DOCUMENTO", "ESTUDIANTE", "CURSO", "ESTADO", "OBSERVACIONES"])

        # Data rows
        for cafeteria, estudiante, grado in results:
            writer.writerow(
                [
                    estudiante.documento,
                    estudiante.nombre,
                    grado.nombre,
                    "PAZ Y SALVO" if cafeteria.estado_cafeteria else "DEUDA",
                    cafeteria.observaciones or "",
                ]
            )

        return output.getvalue()
