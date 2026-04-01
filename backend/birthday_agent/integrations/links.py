from __future__ import annotations

from urllib.parse import quote_plus


def yandex_maps_search_url(query: str) -> str:
    # Пример: https://yandex.ru/maps/?text=кафе%20день%20рождения%20Москва
    return f"https://yandex.ru/maps/?text={quote_plus(query)}"


def two_gis_search_url(query: str) -> str:
    # 2GIS поисковая выдача:
    # Пример: https://2gis.ru/search/%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%20%D0%BA%D0%B0%D1%84%D0%B5
    return f"https://2gis.ru/search/{quote_plus(query)}"


def ozon_search_url(query: str) -> str:
    return f"https://www.ozon.ru/search/?text={quote_plus(query)}"


def wildberries_search_url(query: str) -> str:
    return f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote_plus(query)}"

