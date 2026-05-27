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
    remove_manual_block,
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
    periodo_id: int, grado_id: Optional[int] = None, session: SessionDep = None
):
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
    """
    CAF-RF-12: Genera un reporte CSV con datos legibles (Punto 3).
    """
    # Consulta avanzada con JOIN para traer nombres y documentos
    statement = (
        select(Cafeteria, Estudiante, Grado)
        .join(Estudiante, Cafeteria.estudiante_id == Estudiante.id)
        .join(Grado, Estudiante.grado_id == Grado.id)
        .where(Cafeteria.periodo_id == periodo_id)
    )
    results = session.exec(statement).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Encabezados útiles para la administradora
    writer.writerow(
        [
            "DOCUMENTO",
            "ESTUDIANTE",
            "CURSO",
            "ESTADO",
            "OBSERVACIONES",
            "FECHA ACTUALIZACION",
        ]
    )

    for cafeteria_reg, estudiante_reg, grado_reg in results:
        writer.writerow(
            [
                estudiante_reg.documento,
                estudiante_reg.nombre,
                grado_reg.nombre,
                "PAZ Y SALVO" if cafeteria_reg.estado_cafeteria else "DEUDA",
                cafeteria_reg.observaciones,
                cafeteria_reg.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_cafeteria_periodo_{periodo_id}.csv"
        },
    )


@router.post("/remove-block/{registro_id}")
def remove_block(registro_id: int, usuario_id: int, session: SessionDep):
    """CAF-RF-09: Retirar marca de deuda manualmente."""
    return remove_manual_block(session, registro_id, usuario_id)


@router.post("/bulk-remove-blocks")
def bulk_remove_blocks(data: BulkRemoveBlockSchema, session: SessionDep):
    """CAF-RF-09: Poner al día a varios estudiantes deudores a la vez."""
    try:
        cantidad = bulk_remove_manual_blocks(
            session, data.registro_ids, data.usuario_id
        )
        return {
            "message": f"Se actualizó el estado de {cantidad} registros correctamente."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
