from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ArticleBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int
    views: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Stats(BaseModel):
    total_articles: int
    total_views: int
    most_viewed: List[Article]

    class Config:
        orm_mode = True
