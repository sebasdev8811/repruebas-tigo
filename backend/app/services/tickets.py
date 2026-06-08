from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Ticket


def generar_numero_ticket(db: Session) -> str:
    """Genera un número de ticket con formato TKT-YYYYMMDD-XXXX."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"TKT-{today}-"

    tickets_hoy = (
        db.query(Ticket.numero_ticket)
        .filter(Ticket.numero_ticket.like(f"{prefix}%"))
        .all()
    )

    max_seq = 0
    for (numero,) in tickets_hoy:
        try:
            seq = int(numero.split("-")[-1])
            max_seq = max(max_seq, seq)
        except (ValueError, IndexError):
            continue

    return f"{prefix}{max_seq + 1:04d}"
