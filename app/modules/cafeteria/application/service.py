from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select
from app.modules.cafeteria.infrastructure.models import Cafeteria
from app.modules.enrollment.infrastructure.models import Periodo, Estudiante
from app.modules.auth.infrastructure.models import Usuario


def validate_basic_data(session: Session, periodo_id: int, usuario_id: int):
    """Valida que el periodo y el usuario existan para evitar errores 500."""
    if not session.get(Periodo, periodo_id):
        raise ValueError(f"El periodo con ID {periodo_id} no existe en el sistema.")
    if not session.get(Usuario, usuario_id):
        raise ValueError(f"El usuario con ID {usuario_id} no existe en el sistema.")


def sync_students_to_cafeteria(session: Session, periodo_id: int):
    """Asegura que todos los estudiantes activos estén en la tabla."""
    statement = select(Estudiante).where(Estudiante.activo)
    estudiantes_activos = session.exec(statement).all()

    for est in estudiantes_activos:
        stmt_check = select(Cafeteria).where(
            Cafeteria.estudiante_id == est.id, Cafeteria.periodo_id == periodo_id
        )
        existente = session.exec(stmt_check).first()
        if not existente:
            nuevo = Cafeteria(
                estudiante_id=est.id,
                periodo_id=periodo_id,
                estado_cafeteria=True,  # Paz y Salvo por defecto
                observaciones="Sincronización automática",
            )
            session.add(nuevo)
    session.commit()


def set_manual_no_paz_y_salvo(
    session: Session, registro_id: int, usuario_id: int, observaciones: str
):
    registro = session.get(Cafeteria, registro_id)
    if not registro:
        raise ValueError("El registro de cafetería no existe.")

    # Validamos usuario
    if not session.get(Usuario, usuario_id):
        raise ValueError("El usuario responsable no existe.")

    if not observaciones or len(observaciones.strip()) < 5:
        raise ValueError("Debe registrar una observación válida (mínimo 5 caracteres).")

    registro.estado_cafeteria = False
    registro.observaciones = observaciones
    registro.usuario_id = usuario_id
    registro.updated_at = datetime.now()
    session.add(registro)
    session.commit()
    return registro


def remove_manual_block(session: Session, registro_id: int, usuario_id: int):
    """
    CAF-RF-09: Retira la marca de bloqueo (vuelve a Paz y Salvo).
    """
    registro = session.get(Cafeteria, registro_id)
    if registro:
        registro.estado_cafeteria = True  # Volver a Paz y Salvo
        registro.observaciones = "Bloqueo retirado - Estudiante al día"
        registro.usuario_id = usuario_id
        registro.updated_at = datetime.now()
        session.add(registro)
        session.commit()
    return registro


def bulk_remove_manual_blocks(
    session: Session, registro_ids: List[int], usuario_id: int
) -> int:
    """
    CAF-RF-09: Retira la marca de deuda a múltiples estudiantes a la vez.
    """
    statement = select(Cafeteria).where(Cafeteria.id.in_(registro_ids))
    registros = session.exec(statement).all()

    contador = 0
    for reg in registros:
        reg.estado_cafeteria = True  # Volver a Paz y Salvo
        reg.observaciones = "Deuda retirada masivamente"
        reg.usuario_id = usuario_id
        reg.updated_at = datetime.now()
        session.add(reg)
        contador += 1

    session.commit()
    return contador


def bulk_assign_paz_y_salvo(
    session: Session, periodo_id: int, estudiantes_ids: List[int], usuario_id: int
) -> Dict:
    """CAF-RF-05, 06: Asignación masiva respetando bloqueos manuales."""

    validate_basic_data(session, periodo_id, usuario_id)
    if not estudiantes_ids:
        raise ValueError("No hay estudiantes seleccionados para la operación masiva.")

    total_seleccionados = len(estudiantes_ids)
    total_actualizados = 0
    total_excluidos = 0

    statement = select(Cafeteria).where(
        Cafeteria.periodo_id == periodo_id, Cafeteria.estudiante_id.in_(estudiantes_ids)
    )
    registros = session.exec(statement).all()

    for reg in registros:
        # Si ya está en False (No Paz y Salvo), se considera bloqueado y se excluye
        if reg.estado_cafeteria:
            total_excluidos += 1
        else:
            reg.estado_cafeteria = True
            reg.usuario_id = usuario_id
            reg.updated_at = datetime.now()
            session.add(reg)
            total_actualizados += 1

    session.commit()
    return {
        "total_seleccionados": total_seleccionados,
        "total_actualizados": total_actualizados,
        "total_excluidos": total_excluidos,
    }
