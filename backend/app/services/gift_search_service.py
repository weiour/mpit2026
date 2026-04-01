from typing import List, Dict, Any
import requests
import re
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.wishlist import Wishlist


class GiftSearchService:
    
    @staticmethod
    def search_gifts(query: str, budget: int = None, limit: int = 10) -> List[dict]:
        """
        Поиск подарков через реальные API маркетплейсов и поисковых систем
        """
        results = []
        
        # Поиск через разные источники
        try:
            # 1. Поиск через Google Shopping API (если доступно)
            google_results = GiftSearchService._search_google_shopping(query, budget, limit // 2)
            results.extend(google_results)
        except Exception:
            pass
        
        try:
            # 2. Поиск через Wildberries API
            wb_results = GiftSearchService._search_wildberries(query, budget, limit // 2)
            results.extend(wb_results)
        except Exception:
            pass
        
        try:
            # 3. Поиск через Ozon API
            ozon_results = GiftSearchService._search_ozon(query, budget, limit // 2)
            results.extend(ozon_results)
        except Exception:
            pass
        
        # Валидация и фильтрация результатов
        validated_results = []
        for result in results:
            if GiftSearchService._validate_gift_result(result, budget):
                validated_results.append(result)
        
        # Если ничего не найдено, используем заглушку
        if not validated_results:
            validated_results = GiftSearchService._get_fallback_results(query, budget, limit)
        
        return validated_results[:limit]
    
    @staticmethod
    def _validate_gift_result(result: dict, budget: int = None) -> bool:
        """
        Валидация результата поиска подарка
        """
        try:
            # Проверка обязательных полей (кроме цены - она может быть None для fallback)
            required_fields = ['title', 'url', 'store']
            for field in required_fields:
                if not result.get(field):
                    return False
            
            # Валидация цены (если указана)
            price = result.get('price')
            if price is not None:
                if not isinstance(price, (int, float)) or price <= 0:
                    return False
                
                # Минимальная реалистичная цена (отфильтровываем явно неверные данные)
                if price < 100 and price != 0:
                    return False
                
                # Максимальная цена (для отфильтрования ошибок)
                if price > 10000000:  # 10 миллионов рублей
                    return False
                
                # Проверка бюджета
                if budget is not None and price > budget:
                    return False
            
            # Валидация URL
            url = result.get('url', '')
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Валидация изображения (опционально)
            image = result.get('image', '')
            if image and not image.startswith(('http://', 'https://')):
                return False
            
            # Валидация скидки
            discount = result.get('discount')
            if discount is not None:
                if not isinstance(discount, (int, float)) or discount < 0 or discount > 100:
                    return False
            
            # Валидация рейтинга
            rating = result.get('rating')
            if rating is not None:
                if not isinstance(rating, (int, float)) or rating < 0 or rating > 5:
                    return False
            
            # Валидация количества отзывов
            reviews_count = result.get('reviews_count')
            if reviews_count is not None:
                if not isinstance(reviews_count, int) or reviews_count < 0:
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def _search_google_shopping(query: str, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Поиск через Google Shopping API
        """
        # Формирование URL для поиска Google Shopping
        encoded_query = quote_plus(query)
        url = f"https://www.googleapis.com/customsearch/v1"
        
        params = {
            'key': getattr(settings, 'GOOGLE_API_KEY', ''),
            'cx': getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', ''),
            'q': encoded_query,
            'num': limit,
            'searchType': 'image'
        }
        
        if not params['key']:
            return []
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get('items', []):
            # Извлечение цены из заголовка или сниппета
            price = GiftSearchService._extract_price(item.get('title', '') + ' ' + item.get('snippet', ''))
            
            # Фильтрация по бюджету и валидация цены
            if not price or price < 100:
                continue
            if budget and price > budget:
                continue
            
            results.append({
                'title': item.get('title', ''),
                'description': item.get('snippet', ''),
                'price': price,
                'url': item.get('link', ''),
                'image': item.get('pagemap', {}).get('cse_image', [{}])[0].get('src', ''),
                'store': 'Google Shopping'
            })
        
        return results
    
    @staticmethod
    def _search_wildberries(query: str, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Поиск через Wildberries API с корректным извлечением цен и улучшенной обработкой ошибок
        """
        encoded_query = quote_plus(query)
        url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?TestGroup=no_test&TestID=no_test&app_type=web&curr=rub&query={encoded_query}&resultset=catalog&sort=popular&limit={limit}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://www.wildberries.ru/',
            'Connection': 'keep-alive'
        }
        
        try:
            # Увеличиваем таймаут и добавляем retry логику
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Wildberries API returned status {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            for product in data.get('data', {}).get('products', [])[:limit]:
                # Улучшенное извлечение цены
                price_info = GiftSearchService._extract_wb_price(product)
                
                if not price_info:
                    continue
                
                # Фильтрация по бюджету
                if budget and price_info['price'] > budget:
                    continue
                
                brand = product.get('brand', 'Unknown')
                name = product.get('name', '')
                
                # Получение изображения
                image_url = GiftSearchService._get_wb_image_url(product)
                
                results.append({
                    'title': f"{brand} {name}",
                    'description': product.get('description', f'{brand} {name}'),
                    'price': price_info['price'],
                    'original_price': price_info.get('original_price'),
                    'discount': price_info.get('discount'),
                    'url': f"https://www.wildberries.ru/catalog/{product.get('id', 0)}/detail.aspx",
                    'image': image_url,
                    'store': 'Wildberries',
                    'rating': product.get('rating', 0),
                    'reviews_count': product.get('reviewCount', 0)
                })
            
            return results
            
        except requests.exceptions.Timeout:
            print("Wildberries API timeout - using fallback")
            return GiftSearchService._get_wb_fallback(query, budget, limit)
        except requests.exceptions.ConnectionError:
            print("Wildberries API connection error - using fallback")
            return GiftSearchService._get_wb_fallback(query, budget, limit)
        except requests.exceptions.RequestException as e:
            print(f"Wildberries API request error: {e} - using fallback")
            return GiftSearchService._get_wb_fallback(query, budget, limit)
        except Exception as e:
            print(f"Error searching Wildberries: {e}")
            return []
    
    @staticmethod
    def _extract_wb_price(product: dict) -> dict:
        """
        Извлечение цены из Wildberries продукта с учетом скидок
        """
        try:
            # Текущая цена (в копейках)
            sale_price = product.get('salePriceU', 0)
            if sale_price:
                sale_price = sale_price // 100  # Конвертируем в рубли
            
            # Оригинальная цена до скидки
            original_price = product.get('priceU', 0)
            if original_price:
                original_price = original_price // 100
            
            # Процент скидки
            discount = product.get('sale', 0)
            
            price_info = {
                'price': sale_price or original_price or 0
            }
            
            # Добавляем информацию о скидке если есть
            if original_price and sale_price and original_price > sale_price:
                price_info['original_price'] = original_price
                price_info['discount'] = discount or round((1 - sale_price / original_price) * 100)
            
            # Минимальная валидная цена
            if price_info['price'] < 10:
                return None
            
            return price_info
            
        except Exception:
            return None
    
    @staticmethod
    def _get_wb_image_url(product: dict) -> str:
        """
        Формирование корректного URL изображения Wildberries
        """
        try:
            pic = product.get('pic', '')
            if not pic:
                return ""
            
            # Wildberries использует разные размеры изображений
            # Заменяем cms на big для получения большого изображения
            if 'cms' in pic:
                return pic.replace('cms', 'big')
            
            # Добавляем базовый URL если нужно
            if not pic.startswith('http'):
                return f"https://images.wb.ru/images/{pic}"
            
            return pic
            
        except Exception:
            return ""
    
    @staticmethod
    def _get_wb_fallback(query: str, budget: int = None, limit: int = 3) -> List[dict]:
        """
        Fallback метод для Wildberries - ссылка на поиск без фиктивной цены
        """
        encoded_query = quote_plus(query)
        
        fallback_results = [
            {
                "title": f"Найти '{query.title()}' на Wildberries",
                "description": f"Смотрите реальные цены на товары по запросу '{query}' на Wildberries",
                "price": None,
                "url": f"https://www.wildberries.ru/catalog/0/detail.aspx?search={encoded_query}",
                "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Wildberries_logo.svg/1200px-Wildberries_logo.svg.png",
                "store": "Wildberries",
                "rating": None,
                "reviews_count": None
            }
        ]
        
        return fallback_results[:limit]
    
    @staticmethod
    def _search_ozon(query: str, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Поиск через Ozon с улучшенным парсингом цен и обработкой ошибок
        """
        encoded_query = quote_plus(query)
        url = f"https://www.ozon.ru/search/?text={encoded_query}&from_global=true"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://www.ozon.ru/',
            'Connection': 'keep-alive'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Ozon returned status {response.status_code}")
                return GiftSearchService._get_ozon_fallback(query, budget, limit)
            
            html_content = response.text
            
            # Ищем данные о товарах в разных форматах
            results = []
            
            # Метод 1: Поиск в window.__STATE__
            state_results = GiftSearchService._parse_ozon_state(html_content, budget, limit)
            results.extend(state_results)
            
            # Метод 2: Поиск через регулярные выражения как запасной вариант
            if not results:
                regex_results = GiftSearchService._parse_ozon_regex(html_content, budget, limit)
                results.extend(regex_results)
            
            # Метод 3: Fallback с прямым поиском
            if not results:
                fallback_results = GiftSearchService._get_ozon_fallback(query, budget, limit)
                results.extend(fallback_results)
            
            return results[:limit]
            
        except requests.exceptions.Timeout:
            print("Ozon timeout - using fallback")
            return GiftSearchService._get_ozon_fallback(query, budget, limit)
        except requests.exceptions.ConnectionError:
            print("Ozon connection error - using fallback")
            return GiftSearchService._get_ozon_fallback(query, budget, limit)
        except requests.exceptions.RequestException as e:
            print(f"Ozon request error: {e} - using fallback")
            return GiftSearchService._get_ozon_fallback(query, budget, limit)
        except Exception as e:
            print(f"Error searching Ozon: {e}")
            return []
    
    @staticmethod
    def _parse_ozon_state(html_content: str, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Парсинг данных из window.__STATE__ Ozon
        """
        try:
            # Ищем JSON с данными о товарах
            json_pattern = r'window\.__STATE__\s*=\s*({.*?});'
            match = re.search(json_pattern, html_content, re.DOTALL)
            
            if not match:
                return []
            
            import json
            state_data = json.loads(match.group(1))
            
            results = []
            
            # Извлечение товаров из состояния
            try:
                # Ozon может хранить товары в разных местах структуры
                items = []
                
                # Попытка 1: searching -> items
                items = state_data.get('searching', {}).get('items', [])
                
                # Попытка 2: catalog -> items
                if not items:
                    items = state_data.get('catalog', {}).get('items', [])
                
                # Попытка 3: search -> items
                if not items:
                    items = state_data.get('search', {}).get('items', [])
                
                for item in items[:limit]:
                    product_info = GiftSearchService._extract_ozon_product_info(item)
                    
                    if not product_info:
                        continue
                    
                    # Фильтрация по бюджету
                    if budget and product_info['price'] > budget:
                        continue
                    
                    results.append(product_info)
                    
            except Exception as e:
                print(f"Error parsing Ozon items: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error parsing Ozon state: {e}")
            return []
    
    @staticmethod
    def _extract_ozon_product_info(item: dict) -> dict:
        """
        Извлечение информации о продукте Ozon
        """
        try:
            # Базовая информация
            title = item.get('title', '') or item.get('name', '')
            if not title:
                return None
            
            # Извлечение цены
            price_info = GiftSearchService._extract_ozon_price(item)
            if not price_info or price_info['price'] <= 0:
                return None
            
            # URL товара
            product_id = item.get('id', '') or item.get('productId', '') or item.get('sku', '')
            if not product_id:
                return None
            
            # Изображение
            image = item.get('image', '') or item.get('picture', '') or item.get('imageUrl', '')
            
            # Формируем полный URL
            if image and not image.startswith('http'):
                image = f"https://ozon-st.cdn.net/{image}"
            
            return {
                'title': title,
                'description': item.get('description', title),
                'price': price_info['price'],
                'original_price': price_info.get('original_price'),
                'discount': price_info.get('discount'),
                'url': f"https://www.ozon.ru/product/{product_id}/",
                'image': image,
                'store': 'Ozon',
                'rating': item.get('rating', 0),
                'reviews_count': item.get('reviewsCount', 0)
            }
            
        except Exception as e:
            print(f"Error extracting Ozon product info: {e}")
            return None
    
    @staticmethod
    def _extract_ozon_price(item: dict) -> dict:
        """
        Извлечение цены из товара Ozon
        """
        try:
            # Различные поля где может быть цена
            price_fields = [
                'price', 'finalPrice', 'salePrice', 'currentPrice',
                'priceU', 'finalPriceU', 'salePriceU'
            ]
            
            price = 0
            original_price = 0
            
            # Ищем текущую цену
            for field in price_fields:
                value = item.get(field, 0)
                if value:
                    # Если цена в копейках (заканчивается на U), делим на 100
                    if field.endswith('U') and isinstance(value, int) and value > 10000:
                        price = value // 100
                    else:
                        price = value
                    break
            
            # Ищем оригинальную цену
            original_fields = ['originalPrice', 'oldPrice', 'priceBeforeDiscount', 'listPrice']
            for field in original_fields:
                value = item.get(field, 0)
                if value:
                    if field.endswith('U') and isinstance(value, int) and value > 10000:
                        original_price = value // 100
                    else:
                        original_price = value
                    break
            
            # Расчет скидки
            discount = 0
            if original_price > price and price > 0:
                discount = round((1 - price / original_price) * 100)
            
            price_info = {'price': price}
            
            if original_price > price:
                price_info['original_price'] = original_price
                price_info['discount'] = discount
            
            # Валидация цены
            if price < 10:
                return None
            
            return price_info
            
        except Exception:
            return None
    
    @staticmethod
    def _parse_ozon_regex(html_content: str, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Запасной метод парсинга Ozon через регулярные выражения
        """
        try:
            results = []
            
            # Ищем JSON данные о товарах в скриптах
            script_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
            script_matches = re.findall(script_pattern, html_content, re.DOTALL)
            
            for script_content in script_matches:
                try:
                    import json
                    data = json.loads(script_content)
                    
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                product_info = GiftSearchService._extract_ozon_from_ldjson(item, budget)
                                if product_info:
                                    results.append(product_info)
                    
                except json.JSONDecodeError:
                    continue
            
            return results[:limit]
            
        except Exception:
            return []
    
    @staticmethod
    def _extract_ozon_from_ldjson(item: dict, budget: int = None) -> dict:
        """
        Извлечение товара из LD+JSON Ozon
        """
        try:
            title = item.get('name', '')
            if not title:
                return None
            
            # Цена из offers
            offers = item.get('offers', {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            
            price = offers.get('price', 0)
            if not price or price < 10:
                return None
            
            if budget and price > budget:
                return None
            
            return {
                'title': title,
                'description': item.get('description', title),
                'price': int(price),
                'url': item.get('url', ''),
                'image': item.get('image', ''),
                'store': 'Ozon'
            }
            
        except Exception:
            return None
    
    @staticmethod
    def _get_ozon_fallback(query: str, budget: int = None, limit: int = 3) -> List[dict]:
        """
        Fallback метод для Ozon - ссылка на поиск без фиктивной цены
        """
        encoded_query = quote_plus(query)
        
        fallback_results = [
            {
                "title": f"Найти '{query.title()}' на Ozon",
                "description": f"Смотрите реальные цены на товары по запросу '{query}' на Ozon",
                "price": None,
                "url": f"https://www.ozon.ru/search/?text={encoded_query}&from_global=true",
                "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Ozon_logo.svg/2560px-Ozon_logo.svg.png",
                "store": "Ozon",
                "rating": None,
                "reviews_count": None
            }
        ]
        
        return fallback_results[:limit]
    
    @staticmethod
    def _extract_price(text: str) -> int:
        """
        Извлечение цены из текста
        """
        # Ищем цены в формате: 1500 руб, 1 500₽, $25, etc.
        price_patterns = [
            r'(\d{1,3}(?:[ \s]?\d{3})*(?:[.,]\d+)?)\s*(?:руб|₽|р)',
            r'\$(\d{1,3}(?:[,\s]?\d{3})*(?:\.\d+)?)',
            r'(\d{1,3}(?:[ \s]?\d{3})*(?:[.,]\d+)?)\s*(?:USD|usd)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text.lower())
            if match:
                price_str = match.group(1).replace(' ', '').replace(',', '.')
                try:
                    return int(float(price_str))
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def _get_fallback_results(query: str, budget: int = None, limit: int = 3) -> List[dict]:
        """
        Запасные результаты - ссылки на реальные маркетплейсы без фиктивных цен
        """
        encoded_query = quote_plus(query)
        
        fallback_results = [
            {
                "title": f"Найти '{query.title()}' на Wildberries",
                "description": f"Смотрите реальные цены на товары по запросу '{query}' на Wildberries",
                "price": None,
                "url": f"https://www.wildberries.ru/catalog/0/detail.aspx?search={encoded_query}",
                "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Wildberries_logo.svg/1200px-Wildberries_logo.svg.png",
                "store": "Wildberries",
                "rating": None,
                "reviews_count": None
            },
            {
                "title": f"Найти '{query.title()}' на Ozon",
                "description": f"Смотрите реальные цены на товары по запросу '{query}' на Ozon",
                "price": None,
                "url": f"https://www.ozon.ru/search/?text={encoded_query}&from_global=true",
                "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Ozon_logo.svg/2560px-Ozon_logo.svg.png",
                "store": "Ozon",
                "rating": None,
                "reviews_count": None
            },
            {
                "title": f"Найти '{query.title()}' на Яндекс Маркет",
                "description": f"Смотрите реальные цены на товары по запросу '{query}' на Яндекс Маркет",
                "price": None,
                "url": f"https://market.yandex.ru/search?text={encoded_query}",
                "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Yandex_Market_logo.svg/2560px-Yandex_Market_logo.svg.png",
                "store": "Яндекс Маркет",
                "rating": None,
                "reviews_count": None
            }
        ]
        
        return fallback_results[:limit]
    
    @staticmethod
    def get_recommendations_for_event(event_id: int, db: Session, budget: int = None, limit: int = 10) -> List[dict]:
        """
        Получает рекомендации подарков на основе вишлиста события
        """
        wishlist_items = db.query(Wishlist).filter(Wishlist.event_id == event_id).all()
        
        recommendations = []
        for item in wishlist_items:
            # Ищем похожие товары для каждого элемента вишлиста
            similar_gifts = GiftSearchService.search_gifts(
                query=item.title,
                budget=min(budget, item.price) if budget and item.price else budget,
                limit=max(1, limit // len(wishlist_items))
            )
            
            # Добавляем информацию о связанном элементе вишлиста
            for gift in similar_gifts:
                gift['wishlist_item_title'] = item.title
            
            recommendations.extend(similar_gifts)
        
        return recommendations[:limit]
    
    @staticmethod
    def find_alternatives(wishlist_item_id: int, db: Session, budget: int = None, limit: int = 5) -> List[dict]:
        """
        Находит альтернативы для конкретного элемента вишлиста
        """
        item = db.query(Wishlist).filter(Wishlist.id == wishlist_item_id).first()
        if not item:
            return []
        
        return GiftSearchService.search_gifts(
            query=item.title,
            budget=min(budget, item.price) if budget and item.price else budget,
            limit=limit
        )
    
    @staticmethod
    def _apply_filters(results: List[dict], filter_obj) -> List[dict]:
        """
        Применяет расширенные фильтры к результатам поиска
        """
        filtered_results = results.copy()
        
        # Фильтрация по цене
        if filter_obj.min_price is not None:
            filtered_results = [r for r in filtered_results if r.get('price', 0) >= filter_obj.min_price]
        
        if filter_obj.max_price is not None:
            filtered_results = [r for r in filtered_results if r.get('price', 0) <= filter_obj.max_price]
        
        # Фильтрация по магазинам
        if filter_obj.stores:
            filtered_results = [r for r in filtered_results if r.get('store') in filter_obj.stores]
        
        # Фильтрация по категориям (упрощенная версия)
        if filter_obj.categories:
            filtered_results = [
                r for r in filtered_results 
                if any(category.lower() in r.get('title', '').lower() or 
                      category.lower() in r.get('description', '').lower() 
                      for category in filter_obj.categories)
            ]
        
        # Фильтрация по рейтингу
        if filter_obj.min_rating is not None:
            filtered_results = [
                r for r in filtered_results 
                if r.get('rating', 0) >= filter_obj.min_rating
            ]
        
        # Фильтрация по наличию скидок
        if filter_obj.has_discount is not None:
            if filter_obj.has_discount:
                # Только товары со скидками
                filtered_results = [
                    r for r in filtered_results 
                    if r.get('discount') is not None and r.get('discount') > 0
                ]
            else:
                # Только товары без скидок
                filtered_results = [
                    r for r in filtered_results 
                    if r.get('discount') is None or r.get('discount') == 0
                ]
        
        # Фильтрация по минимальному проценту скидки
        if filter_obj.min_discount_percent is not None:
            filtered_results = [
                r for r in filtered_results 
                if r.get('discount') is not None and r.get('discount') >= filter_obj.min_discount_percent
            ]
        
        return filtered_results
