from sqlmodel import Session, select
import uuid
from db.models.analysis import Analysis  

class AnalysisRepository:
    @staticmethod
    def save_analysis(session: Session, user_id: uuid.UUID, job_description: str, ai_result: dict) -> Analysis:
        """
        Takes the raw JSON output from the AI and saves it to PostgreSQL.
        """
        db_analysis = Analysis(
            user_id=user_id,
            job_description=job_description,
            match_percentage=ai_result.get("match_percentage", 0),
            executive_summary=ai_result.get("executive_summary", ""),
            missing_skills=ai_result.get("missing_skills", [])
        )
        
        session.add(db_analysis)
        session.commit()
        session.refresh(db_analysis)
        
        return db_analysis
    

def get_analysis_for_user(session: Session, user_id: uuid.UUID) -> list[Analysis]:
    stmt = select(Analysis).where(Analysis.user_id == user_id)
    return session.exec(stmt).all()

def get_analysis_by_id(session: Session, analysis_id: uuid.UUID,user_id: uuid.UUID) -> Analysis:
    stmt = select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    return session.exec(stmt).first()


def delete_analysis_by_id(session: Session, analysis_id: uuid.UUID,user_id: uuid.UUID) -> bool:
    stmt = select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    analysis = session.exec(stmt).first()
    if analysis:
        session.delete(analysis)
        session.commit()
        return True
    return False