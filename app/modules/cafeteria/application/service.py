from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select, col  # Importamos col
from app.modules.cafeteria.infrastructure.models import Cafeteria
from app.modules.enrollment.infrastructure.models import Estudiante, Periodo
from app.modules.auth.infrastructure.models import Usuario


def validate_basic_data(session: Session, periodo_id: int, usuario_id: int) -> None:
    if not session.get(Periodo, periodo_id):
        raise ValueError(f"El periodo con ID {periodo_id} no existe.")
    if not session.get(Usuario, usuario_id):
        raise ValueError(f"El usuario con ID {usuario_id} no existe.")


def sync_students_to_cafeteria(session: Session, periodo_id: int) -> None:
    statement = select(Estudiante).where(Estudiante.activo)
    estudiantes_activos = session.exec(statement).all()

    for est in estudiantes_activos:
        if est.id is None:
            continue

        stmt_check = select(Cafeteria).where(
            Cafeteria.estudiante_id == est.id, Cafeteria.periodo_id == periodo_id
        )
        if not session.exec(stmt_check).first():
            nuevo = Cafeteria(
                estudiante_id=est.id,
                periodo_id=periodo_id,
                estado_cafeteria=True,
                observaciones="Sincronización automática",
            )
            session.add(nuevo)
    session.commit()


def set_manual_no_paz_y_salvo(
    session: Session, registro_id: int, usuario_id: int, observaciones: str
) -> Cafeteria:
    registro = session.get(Cafeteria, registro_id)
    if not registro:
        raise ValueError("El registro no existe.")

    if not session.get(Usuario, usuario_id):
        raise ValueError("El usuario responsable no existe.")

    if not observaciones or len(observaciones.strip()) < 5:
        raise ValueError("Debe registrar una observación válida.")

    registro.estado_cafeteria = False
    registro.observaciones = observaciones
    registro.usuario_id = usuario_id
    registro.updated_at = datetime.now()
    session.add(registro)
    session.commit()
    session.refresh(registro)
    return registro


def bulk_assign_paz_y_salvo(
    session: Session, periodo_id: int, estudiantes_ids: List[int], usuario_id: int
) -> Dict[str, int]:
    validate_basic_data(session, periodo_id, usuario_id)

    if not estudiantes_ids:
        raise ValueError("No hay estudiantes seleccionados.")

    # USAMOS col() para que el linter reconozca .in_()
    statement = select(Cafeteria).where(
        Cafeteria.periodo_id == periodo_id,
        col(Cafeteria.estudiante_id).in_(estudiantes_ids),
    )
    registros = session.exec(statement).all()

    actualizados = 0
    excluidos = 0
    for reg in registros:
        if not reg.estado_cafeteria:
            excluidos += 1
        else:
            reg.estado_cafeteria = True
            reg.usuario_id = usuario_id
            reg.updated_at = datetime.now()
            session.add(reg)
            actualizados += 1
    session.commit()
    return {
        "total_seleccionados": len(estudiantes_ids),
        "total_actualizados": actualizados,
        "total_excluidos": excluidos,
    }


def bulk_remove_manual_blocks(
    session: Session, registro_ids: List[int], usuario_id: int
) -> int:
    # USAMOS col() para que el linter reconozca .in_()
    statement = select(Cafeteria).where(col(Cafeteria.id).in_(registro_ids))
    registros = session.exec(statement).all()

    contador = 0
    for reg in registros:
        reg.estado_cafeteria = True
        reg.observaciones = "Deuda retirada masivamente"
        reg.usuario_id = usuario_id
        reg.updated_at = datetime.now()
        session.add(reg)
        contador += 1
    session.commit()
    return contador
