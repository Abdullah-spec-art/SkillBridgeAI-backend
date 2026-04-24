import uuid
from sqlmodel import Session, select
from db.models.analysis import Analysis

def create_analysis(db: Session, analysis: Analysis) -> Analysis:
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis

def get_all_by_user(db: Session, user_id: uuid.UUID) -> list[Analysis]:
    # Returns raw DB models, ordered newest to oldest
    stmt = select(Analysis).where(Analysis.user_id == user_id).order_by(Analysis.created_at.desc())
    return db.exec(stmt).all()

def get_by_id(db: Session, analysis_id: uuid.UUID) -> Analysis | None:
    # Pure fetch. Returns None if not found. No ownership checks here!
    return db.get(Analysis, analysis_id)

def delete_analysis(db: Session, analysis: Analysis) -> None:
    # Blindly deletes the object passed to it
    db.delete(analysis)
    db.commit()