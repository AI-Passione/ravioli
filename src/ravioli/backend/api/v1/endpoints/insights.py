from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from datetime import datetime, UTC, timedelta

from ravioli.backend.core.database import get_db
from ravioli.backend.core import models, schemas

router = APIRouter()


@router.get("/stats", response_model=schemas.InsightStats)
def get_insight_stats(db: Session = Depends(get_db)):
    """BANs: verified count, total analyses, and contributing analyses (distinct sources with ≥1 verified insight)."""
    verified_count = db.query(func.count(models.Insight.id)).filter(
        models.Insight.is_verified == True
    ).scalar() or 0

    analyses_count = db.query(func.count(models.Analysis.id)).scalar() or 0

    contributors_count = db.query(
        func.count(func.distinct(models.Insight.analysis_id))
    ).filter(models.Insight.is_verified == True).scalar() or 0

    return schemas.InsightStats(
        verified_count=verified_count,
        analyses_count=analyses_count,
        contributors_count=contributors_count,
    )


@router.get("/summary")
async def get_insights_summary(days: int = 7, db: Session = Depends(get_db)):
    """AI-generated executive summary of all verified insights within the last `days` days."""
    since = datetime.now(UTC) - timedelta(days=days)
    insights = (
        db.query(models.Insight)
        .filter(models.Insight.is_verified == True, models.Insight.created_at >= since)
        .order_by(models.Insight.created_at.desc())
        .all()
    )
    contents = [i.content for i in insights]

    from ravioli.ai.agents.Kowalski import KowalskiAgent
    agent = KowalskiAgent(db)
    summary = await agent.generate_insights_summary(contents, days)
    return {"summary": summary, "insight_count": len(contents), "days": days}


@router.get("/review-queue", response_model=List[schemas.Insight])
def get_review_queue(db: Session = Depends(get_db)):
    """Unverified insights awaiting operator review, newest first."""
    return (
        db.query(models.Insight)
        .filter(models.Insight.is_verified == False)
        .order_by(models.Insight.created_at.desc())
        .all()
    )


@router.get("/feed", response_model=List[schemas.Insight])
def get_insights_feed(days: int = 30, db: Session = Depends(get_db)):
    """Verified insights, newest first, used for the News Feed."""
    since = datetime.now(UTC) - timedelta(days=days)
    return (
        db.query(models.Insight)
        .filter(models.Insight.is_verified == True, models.Insight.created_at >= since)
        .order_by(models.Insight.created_at.desc())
        .all()
    )


@router.patch("/{insight_id}/verify", response_model=schemas.Insight)
def verify_insight(insight_id: UUID, db: Session = Depends(get_db)):
    """Mark an insight as verified."""
    insight = db.query(models.Insight).filter(models.Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    insight.is_verified = True
    insight.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(insight)
    return insight


@router.patch("/{insight_id}/reject", response_model=schemas.Insight)
def reject_insight(insight_id: UUID, db: Session = Depends(get_db)):
    """Remove an insight from the review queue (soft-reject: delete the row)."""
    insight = db.query(models.Insight).filter(models.Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    db.delete(insight)
    db.commit()
    return insight


@router.get("/", response_model=List[schemas.Insight])
def list_insights(db: Session = Depends(get_db)):
    return db.query(models.Insight).order_by(models.Insight.created_at.desc()).all()
