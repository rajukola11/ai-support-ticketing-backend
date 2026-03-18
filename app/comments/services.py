from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID

from app.comments.models import Comment
from app.comments.schemas import CommentCreate, CommentUpdate


# -----------------------------
# Create Comment
# -----------------------------
def create_comment(
    db: Session,
    ticket_id: UUID,
    user_id: UUID,
    comment_data: CommentCreate,
) -> Comment:
    comment = Comment(
        ticket_id=ticket_id,
        user_id=user_id,
        content=comment_data.content,
        is_internal=comment_data.is_internal,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# -----------------------------
# Get Comments for Ticket
# -----------------------------
def get_comments(
    db: Session,
    ticket_id: UUID,
    include_internal: bool = False,
) -> list[Comment]:
    query = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.ticket_id == ticket_id)
    )
    if not include_internal:
        query = query.filter(Comment.is_internal == False)
    return query.order_by(Comment.created_at.asc()).all()


# -----------------------------
# Get Single Comment
# -----------------------------
def get_comment_by_id(db: Session, comment_id: UUID) -> Optional[Comment]:
    return (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.id == comment_id)
        .first()
    )


# -----------------------------
# Update Comment
# -----------------------------
def update_comment(db: Session, comment: Comment, update_data: CommentUpdate) -> Comment:
    comment.content = update_data.content
    db.commit()
    db.refresh(comment)
    return comment


# -----------------------------
# Delete Comment
# -----------------------------
def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()