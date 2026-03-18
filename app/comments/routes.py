from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.auth.security import get_current_user
from app.auth.models import User, UserRole
from app.tickets.services import get_ticket_by_id
from app.comments import services, schemas

router = APIRouter(tags=["Comments"])


def is_agent_or_admin(user: User) -> bool:
    return user.role in (UserRole.SUPPORT_AGENT, UserRole.ADMIN)


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


# -----------------------------
# Add Comment to Ticket
# -----------------------------
@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: UUID,
    comment_data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Only ticket owner, agents, or admins can comment
    if not is_agent_or_admin(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Only agents/admins can post internal notes
    if comment_data.is_internal and not is_agent_or_admin(current_user):
        comment_data.is_internal = False

    return services.create_comment(db, ticket_id, current_user.id, comment_data)


# -----------------------------
# List Comments on Ticket
# -----------------------------
@router.get(
    "/tickets/{ticket_id}/comments",
    response_model=list[schemas.CommentResponse],
)
def list_comments(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if not is_agent_or_admin(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Agents/admins see internal notes too, regular users don't
    include_internal = is_agent_or_admin(current_user)
    return services.get_comments(db, ticket_id, include_internal=include_internal)


# -----------------------------
# Edit Comment
# -----------------------------
@router.patch(
    "/tickets/{ticket_id}/comments/{comment_id}",
    response_model=schemas.CommentResponse,
)
def edit_comment(
    ticket_id: UUID,
    comment_id: UUID,
    update_data: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = services.get_comment_by_id(db, comment_id)

    if not comment or comment.ticket_id != ticket_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Only the author can edit their comment
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own comments")

    return services.update_comment(db, comment, update_data)


# -----------------------------
# Delete Comment
# -----------------------------
@router.delete(
    "/tickets/{ticket_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    ticket_id: UUID,
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = services.get_comment_by_id(db, comment_id)

    if not comment or comment.ticket_id != ticket_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Author or admin can delete
    if comment.user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    services.delete_comment(db, comment)