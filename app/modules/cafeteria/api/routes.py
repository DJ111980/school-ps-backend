import csv
import io
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select
from app.core.db import SessionDep

from app.modules.cafeteria.infrastructure.models import Cafeteria
from app.modules.enrollment.infrastructure.models import Estudiante, Grado
from app.modules.cafeteria.application.service import (
    sync_students_to_cafeteria,
    set_manual_no_paz_y_salvo,
    bulk_assign_paz_y_salvo,
    bulk_remove_manual_blocks,
)
from app.modules.cafeteria.schemas.schemas import (
    ManualBlockSchema,
    BulkPazSalvoSchema,
    BulkRemoveBlockSchema,
)

router = APIRouter(prefix="/cafeteria", tags=["Cafeteria"])


@router.get("/list/{periodo_id}")
def list_cafeteria_students(
    periodo_id: int, session: SessionDep, grado_id: Optional[int] = None
):
    # Eliminamos el = None en session para cumplir con PEP 484
    sync_students_to_cafeteria(session, periodo_id)
    statement = select(Cafeteria).where(Cafeteria.periodo_id == periodo_id)
    if grado_id:
        statement = statement.join(Estudiante).where(Estudiante.grado_id == grado_id)
    return session.exec(statement).all()


@router.post("/manual-block")
def manual_block(data: ManualBlockSchema, session: SessionDep):
    try:
        return set_manual_no_paz_y_salvo(
            session, data.registro_id, data.usuario_id, data.observaciones
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-paz-y-salvo")
def bulk_paz_y_salvo(data: BulkPazSalvoSchema, session: SessionDep):
    try:
        return bulk_assign_paz_y_salvo(
            session, data.periodo_id, data.estudiantes_ids, data.usuario_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-remove-blocks")
def bulk_remove_blocks(data: BulkRemoveBlockSchema, session: SessionDep):
    try:
        cantidad = bulk_remove_manual_blocks(
            session, data.registro_ids, data.usuario_id
        )
        return {
            "message": f"Se actualizó el estado de {cantidad} registros correctamente."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{estudiante_id}/{periodo_id}")
def get_student_status(estudiante_id: int, periodo_id: int, session: SessionDep):
    statement = select(Cafeteria).where(
        Cafeteria.estudiante_id == estudiante_id, Cafeteria.periodo_id == periodo_id
    )
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="No encontrado")
    return result


@router.get("/export/{periodo_id}")
def export_cafeteria_report(periodo_id: int, session: SessionDep):
    # Corregimos el JOIN para que Mypy no se queje del tipo bool
    statement = (
        select(Cafeteria, Estudiante, Grado)
        .where(Cafeteria.estudiante_id == Estudiante.id)
        .where(Estudiante.grado_id == Grado.id)
        .where(Cafeteria.periodo_id == periodo_id)
    )
    results = session.exec(statement).all()

    output = io.StringIO()  # type: ignore[abstract]
    writer = csv.writer(output)
    writer.writerow(
        ["DOCUMENTO", "ESTUDIANTE", "CURSO", "ESTADO", "OBSERVACIONES", "FECHA"]
    )

    for cafeteria_reg, estudiante_reg, grado_reg in results:
        # Validamos que updated_at no sea None antes de usar strftime
        fecha_str = (
            cafeteria_reg.updated_at.strftime("%Y-%m-%d")
            if cafeteria_reg.updated_at
            else "N/A"
        )

        writer.writerow(
            [
                estudiante_reg.documento,
                estudiante_reg.nombre,
                grado_reg.nombre,
                "PAZ Y SALVO" if cafeteria_reg.estado_cafeteria else "DEUDA",
                cafeteria_reg.observaciones or "",
                fecha_str,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_cafeteria_{periodo_id}.csv"
        },
    )
