from pydantic import BaseModel, Field, validator
from typing import Optional, List


class GiftSearchResponse(BaseModel):
    title: str = Field(..., description="Название товара")
    description: str = Field(..., description="Описание товара")
    price: Optional[int] = Field(None, description="Текущая цена в рублях (None если неизвестна)")
    url: str = Field(..., description="Ссылка на товар")
    image: str = Field(..., description="URL изображения товара")
    store: str = Field(..., description="Название магазина")
    original_price: Optional[int] = Field(None, description="Оригинальная цена до скидки")
    discount: Optional[int] = Field(None, description="Процент скидки")
    rating: Optional[float] = Field(None, description="Рейтинг товара")
    reviews_count: Optional[int] = Field(None, description="Количество отзывов")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Цена не может быть отрицательной')
        return v
    
    @validator('original_price')
    def validate_original_price(cls, v, values):
        if v is not None and 'price' in values and v < values['price']:
            raise ValueError('Оригинальная цена не может быть меньше текущей')
        return v
    
    @validator('discount')
    def validate_discount(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Скидка должна быть в диапазоне от 0 до 100')
        return v


class GiftRecommendationResponse(BaseModel):
    title: str = Field(..., description="Название товара")
    description: str = Field(..., description="Описание товара")
    price: Optional[int] = Field(None, description="Текущая цена в рублях (None если неизвестна)")
    url: str = Field(..., description="Ссылка на товар")
    image: str = Field(..., description="URL изображения товара")
    store: str = Field(..., description="Название магазина")
    wishlist_item_title: Optional[str] = Field(None, description="Название связанного элемента вишлиста")
    original_price: Optional[int] = Field(None, description="Оригинальная цена до скидки")
    discount: Optional[int] = Field(None, description="Процент скидки")
    rating: Optional[float] = Field(None, description="Рейтинг товара")
    reviews_count: Optional[int] = Field(None, description="Количество отзывов")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v


class GiftSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="Поисковый запрос")
    budget: Optional[int] = Field(None, ge=0, description="Максимальный бюджет")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Количество результатов")
    include_discounts: Optional[bool] = Field(True, description="Включать товары со скидками")
    min_discount: Optional[int] = Field(None, ge=0, le=100, description="Минимальный процент скидки")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Поисковый запрос не может быть пустым')
        return v.strip()
    
    @validator('min_discount')
    def validate_min_discount(cls, v, values):
        if v is not None and v > 0 and not values.get('include_discounts', True):
            raise ValueError('Для фильтрации по скидкам нужно включить include_discounts')
        return v


class GiftFilter(BaseModel):
    min_price: Optional[int] = Field(None, ge=0, description="Минимальная цена")
    max_price: Optional[int] = Field(None, ge=0, description="Максимальная цена")
    stores: Optional[List[str]] = Field(None, description="Список предпочтительных магазинов")
    categories: Optional[List[str]] = Field(None, description="Список категорий товаров")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Минимальный рейтинг")
    has_discount: Optional[bool] = Field(None, description="Только товары со скидками")
    min_discount_percent: Optional[int] = Field(None, ge=0, le=100, description="Минимальный процент скидки")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('Максимальная цена не может быть меньше минимальной')
        return v
    
    @validator('min_rating')
    def validate_rating(cls, v):
        if v is not None and not (0 <= v <= 5):
            raise ValueError('Рейтинг должен быть в диапазоне от 0 до 5')
        return v


class PriceHistory(BaseModel):
    price: int = Field(..., description="Цена в рублях")
    date: str = Field(..., description="Дата цены")
    store: str = Field(..., description="Магазин")


class GiftAnalytics(BaseModel):
    product_id: str = Field(..., description="ID товара")
    title: str = Field(..., description="Название товара")
    store: str = Field(..., description="Магазин")
    current_price: int = Field(..., description="Текущая цена")
    original_price: Optional[int] = Field(None, description="Оригинальная цена")
    discount_percent: Optional[int] = Field(None, description="Процент скидки")
    price_history: List[PriceHistory] = Field(default_factory=list, description="История цен")
    best_price: Optional[int] = Field(None, description="Лучшая цена за период")
    price_trend: Optional[str] = Field(None, description="Тренд цены: up/down/stable")
