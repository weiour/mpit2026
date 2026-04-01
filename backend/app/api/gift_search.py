from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.gift_search import (
    GiftSearchResponse, 
    GiftRecommendationResponse, 
    GiftSearchRequest,
    GiftFilter
)
from app.services.gift_search_service import GiftSearchService

router = APIRouter()


@router.post("/gifts/search", response_model=List[GiftSearchResponse])
def search_gifts(
    request: GiftSearchRequest,
    filter: Optional[GiftFilter] = None,
    db: Session = Depends(get_db)
):
    """
    Поиск подарков по запросу с фильтрацией
    """
    try:
        results = GiftSearchService.search_gifts(
            query=request.query,
            budget=request.budget,
            limit=request.limit
        )
        
        # Применяем дополнительные фильтры
        if filter:
            results = GiftSearchService._apply_filters(results, filter)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске подарков: {str(e)}"
        )


@router.get("/gifts/search", response_model=List[GiftSearchResponse])
def search_gifts_get(
    query: str = Query(..., min_length=1, max_length=200, description="Поисковый запрос"),
    budget: Optional[int] = Query(None, ge=0, description="Максимальный бюджет"),
    limit: int = Query(10, ge=1, le=50, description="Количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Поиск подарков по запросу (GET метод)
    """
    try:
        results = GiftSearchService.search_gifts(
            query=query,
            budget=budget,
            limit=limit
        )
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске подарков: {str(e)}"
        )


@router.get("/events/{event_id}/gift-recommendations", response_model=List[GiftRecommendationResponse])
def get_gift_recommendations(
    event_id: int,
    budget: Optional[int] = Query(None, ge=0, description="Максимальный бюджет"),
    limit: int = Query(10, ge=1, le=50, description="Количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Получить рекомендации подарков на основе вишлиста события
    """
    try:
        recommendations = GiftSearchService.get_recommendations_for_event(
            event_id=event_id, 
            db=db, 
            budget=budget,
            limit=limit
        )
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении рекомендаций: {str(e)}"
        )


@router.get("/wishlist/{item_id}/alternatives", response_model=List[GiftSearchResponse])
def get_wishlist_alternatives(
    item_id: int,
    budget: Optional[int] = Query(None, ge=0, description="Максимальный бюджет"),
    limit: int = Query(5, ge=1, le=20, description="Количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Найти альтернативы для элемента вишлиста
    """
    try:
        alternatives = GiftSearchService.find_alternatives(
            wishlist_item_id=item_id,
            db=db,
            budget=budget,
            limit=limit
        )
        return alternatives
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске альтернатив: {str(e)}"
        )


@router.get("/stores", response_model=List[str])
def get_available_stores():
    """
    Получить список доступных магазинов
    """
    return ["Wildberries", "Ozon", "Яндекс Маркет", "Google Shopping"]


@router.get("/categories", response_model=List[str])
def get_popular_categories():
    """
    Получить список популярных категорий подарков
    """
    return [
        "Электроника", "Книги", "Одежда", "Украшения", 
        "Косметика", "Игры и развлечения", "Спорт и туризм",
        "Дом и сад", "Автотовары", "Хобби и творчество"
    ]
