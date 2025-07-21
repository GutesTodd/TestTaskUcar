import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import logging

DB_PATH = "reviews.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(DB_PATH):
        init_db()
        logging.info("База данных создана!")
    else:
        logging.info("База данных уже существует!")
    yield

app = FastAPI(lifespan=lifespan)

class WordConsts:
    POSITIVE = ["хорош", "люблю", "отлично", "супер", "прекрасно"]
    NEGATIVE = ["плохо", "ненавиж", "ужас", "баг", "тормозит"]

def detect_sentiment(text: str) -> str:
    text = text.lower()
    if any(word in text for word in WordConsts.POSITIVE):
        return "positive"
    elif any(word in text for word in WordConsts.NEGATIVE):
        return "negative"
    return "neutral"

class ReviewIn(BaseModel):
    text: str

@app.post("/reviews")
def create_review(review: ReviewIn):
    sentiment = detect_sentiment(review.text)
    created_at = datetime.now()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review.text, sentiment, created_at)
    )
    review_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": review_id,
        "text": review.text,
        "sentiment": sentiment,
        "created_at": created_at
    }

@app.get("/reviews")
def get_reviews(sentiment: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    if sentiment:
        cur.execute("SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?", (sentiment,))
    else:
        cur.execute("SELECT id, text, sentiment, created_at FROM reviews")
    
    rows = cur.fetchall()
    conn.close()

    return [
        {"id": row[0], "text": row[1], "sentiment": row[2], "created_at": row[3]}
        for row in rows
    ]
