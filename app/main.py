from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Base, Question

app = FastAPI(title="Questions API", version="1.0.0")


class QuestionCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    source: Optional[str] = None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    category: Optional[str] = None
    source: Optional[str] = None


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "Questions API funcionando",
        "endpoints": [
            "/questions",
            "/questions/{id}",
            "/questions/category/{category}",
            "/questions/search?query=...",
            "/stats",
            "/questions [POST]",
        ],
    }


@app.get("/questions")
def list_questions(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    questions = db.query(Question).offset(skip).limit(limit).all()
    return questions


@app.get("/questions/search")
def search_questions(query: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .filter(Question.question.ilike(f"%{query}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return questions


@app.post("/questions", response_model=QuestionResponse, status_code=201)
def create_question(question_data: QuestionCreate, db: Session = Depends(get_db)):
    question = Question(
        question=question_data.question,
        answer=question_data.answer,
        category=question_data.category,
        source=question_data.source,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@app.get("/questions/category/{category}")
def list_questions_by_category(category: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .filter(Question.category == category)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return questions


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Question).count()
    category_counts = (
        db.query(Question.category, func.count(Question.id))
        .group_by(Question.category)
        .all()
    )
    return {
        "total_questions": total,
        "questions_by_category": {category or "Sin categoría": count for category, count in category_counts},
    }


@app.get("/questions/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return {"error": "Pregunta no encontrada"}
    return question
