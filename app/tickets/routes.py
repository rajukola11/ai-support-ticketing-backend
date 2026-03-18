from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.auth.security import get_current_user
from app.auth.models import User, UserRole
from app.tickets import services, schemas
from app.tickets.models import TicketStatus

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def is_support_agent(user: User) -> bool:
    return user.role in (UserRole.SUPPORT_AGENT, UserRole.ADMIN)


# -----------------------------
# Create Ticket
# -----------------------------
@router.post("/", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.create_ticket(db, ticket_data, user_id=current_user.id)


# -----------------------------
# List Tickets
# Admin sees all, user sees own
# -----------------------------
@router.get("/", response_model=list[schemas.TicketListResponse])
def list_tickets(
    status: Optional[TicketStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if is_admin(current_user):
        return services.get_all_tickets(db, status=status, skip=skip, limit=limit)
    return services.get_tickets_by_user(db, user_id=current_user.id, status=status, skip=skip, limit=limit)


# -----------------------------
# Get Single Ticket
# -----------------------------
@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = services.get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Only owner, support agents, or admins can view
    if not is_support_agent(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ticket


# -----------------------------
# Update Ticket
# -----------------------------
@router.patch("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: UUID,
    update_data: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = services.get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Only owner can update their own ticket (but not change status/assignment)
    # Support agents and admins can update everything
    if not is_support_agent(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Regular users cannot change status or assign tickets
    if not is_support_agent(current_user):
        update_data.status = None
        update_data.assigned_to = None

    return services.update_ticket(db, ticket, update_data)


# -----------------------------
# Close Ticket
# -----------------------------
@router.post("/{ticket_id}/close", response_model=schemas.TicketResponse)
def close_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = services.get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if not is_support_agent(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already closed")

    return services.close_ticket(db, ticket)


# -----------------------------
# Delete Ticket (admin only)
# -----------------------------
@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    ticket = services.get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    services.delete_ticket(db, ticket)