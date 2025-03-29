from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from datetime import datetime

# Database imports
from database import SessionLocal, engine
import models
import schemas

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Articles Website")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Homepage with site information"""
    articles = db.query(models.Article).order_by(models.Article.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("index.html", {"request": request, "articles": articles})

@app.get("/articles", response_class=HTMLResponse)
async def articles_list(request: Request, db: Session = Depends(get_db)):
    """List all articles"""
    articles = db.query(models.Article).order_by(models.Article.created_at.desc()).all()
    return templates.TemplateResponse("articles.html", {"request": request, "articles": articles})

@app.get("/articles/{article_id}", response_class=HTMLResponse)
async def article_detail(request: Request, article_id: int, db: Session = Depends(get_db)):
    """Show article details and increment view count"""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    article.views += 1
    db.commit()
    
    return templates.TemplateResponse("article_detail.html", {"request": request, "article": article})

# API endpoints for the Telegram bot
@app.post("/api/articles", response_model=schemas.Article)
async def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    """Create a new article (used by Telegram bot)"""
    db_article = models.Article(
        title=article.title,
        content=article.content,
        image_url=article.image_url,
        created_at=datetime.now()
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@app.delete("/api/articles/{article_id}", response_model=schemas.Article)
async def delete_article(article_id: int, db: Session = Depends(get_db)):
    """Delete an article (used by Telegram bot)"""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return article

@app.get("/api/articles", response_model=List[schemas.Article])
async def get_articles(db: Session = Depends(get_db)):
    """Get all articles (used by Telegram bot)"""
    articles = db.query(models.Article).all()
    return articles

@app.get("/api/stats", response_model=schemas.Stats)
async def get_stats(db: Session = Depends(get_db)):
    """Get site statistics (used by Telegram bot)"""
    total_articles = db.query(models.Article).count()
    total_views = db.query(models.Article).with_entities(models.Article.views).all()
    total_views = sum([view[0] for view in total_views])
    
    # Get most viewed articles
    most_viewed = db.query(models.Article).order_by(models.Article.views.desc()).limit(5).all()
    
    return {
        "total_articles": total_articles,
        "total_views": total_views,
        "most_viewed": most_viewed
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
