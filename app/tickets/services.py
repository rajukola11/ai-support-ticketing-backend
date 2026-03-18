from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.tickets.models import Ticket, TicketStatus
from app.tickets.schemas import TicketCreate, TicketUpdate


# -----------------------------
# Create Ticket
# -----------------------------
def create_ticket(db: Session, ticket_data: TicketCreate, user_id: UUID) -> Ticket:
    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        category=ticket_data.category,
        user_id=user_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


# -----------------------------
# Get Ticket by ID
# -----------------------------
def get_ticket_by_id(db: Session, ticket_id: UUID) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


# -----------------------------
# Get All Tickets (admin)
# -----------------------------
def get_all_tickets(
    db: Session,
    status: Optional[TicketStatus] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Ticket]:
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


# -----------------------------
# Get Tickets by User
# -----------------------------
def get_tickets_by_user(
    db: Session,
    user_id: UUID,
    status: Optional[TicketStatus] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Ticket]:
    query = db.query(Ticket).filter(Ticket.user_id == user_id)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


# -----------------------------
# Update Ticket
# -----------------------------
def update_ticket(db: Session, ticket: Ticket, update_data: TicketUpdate) -> Ticket:
    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


# -----------------------------
# Close Ticket
# -----------------------------
def close_ticket(db: Session, ticket: Ticket) -> Ticket:
    ticket.status = TicketStatus.CLOSED
    db.commit()
    db.refresh(ticket)
    return ticket


# -----------------------------
# Delete Ticket
# -----------------------------
def delete_ticket(db: Session, ticket: Ticket) -> None:
    db.delete(ticket)
    db.commit()