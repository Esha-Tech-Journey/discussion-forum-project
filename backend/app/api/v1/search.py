from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import (
    CommentSearchResponse,
    ThreadSearchResponse,
)
from app.services.search_service import (
    SearchService,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


# ==============================
# Search Threads
# ==============================

@router.get(
    "/threads",
    response_model=ThreadSearchResponse
)
def search_threads(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    searchIn: str = Query("all", pattern="^(all|title|content|tags)$"),
    sortBy: str = Query("relevance", pattern="^(relevance|recent|popular)$"),
    db: Session = Depends(get_db),
):

    return SearchService.search_threads(
        db,
        q,
        page=page,
        size=size,
        search_in=searchIn,
        sort_by=sortBy,
    )


@router.get(
    "/comments",
    response_model=CommentSearchResponse
)
def search_comments(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return SearchService.search_comments(
        db,
        q,
        page=page,
        size=size,
    )
