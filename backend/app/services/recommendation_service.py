from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatMessage
from app.models.event import Event
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationMetaOut,
    VenueRecommendationOut,
    VenueRecommendationsOut,
)
from birthday_agent.integrations.links import two_gis_search_url, yandex_maps_search_url


FORMAT_RULES: dict[str, dict[str, list[str]]] = {
    "restaurant": {
        "queries": [
            "ресторан для дня рождения",
            "кафе для дня рождения",
            "банкетный зал",
            "лофт для вечеринки",
            "караоке-клуб",
        ],
        "required": [
            "ресторан",
            "кафе",
            "банкет",
            "банкетный зал",
            "лофт",
            "бар",
            "паб",
            "караоке",
            "гастробар",
            "фудхолл",
            "event hall",
        ],
        "forbidden": [
            "автомастер",
            "автосервис",
            "шиномонтаж",
            "автозапчаст",
            "мойка",
            "гостиниц",
            "отель",
            "хостел",
            "стомат",
            "клиник",
            "аптек",
            "больниц",
            "поликлиник",
            "жилой комплекс",
            "офис",
            "склад",
            "заправк",
        ],
    },
    "outdoor": {
        "queries": [
            "загородный клуб для праздника",
            "база отдыха для компании",
            "площадка для мероприятия на природе",
            "парк с беседками",
            "глэмпинг для компании",
        ],
        "required": [
            "загород",
            "база отдыха",
            "парк",
            "природ",
            "глэмпинг",
            "кемпинг",
            "турбаза",
            "беседк",
            "усадьба",
            "пляж",
            "эко",
            "коттедж",
        ],
        "forbidden": [
            "автомастер",
            "автосервис",
            "шиномонтаж",
            "стомат",
            "клиник",
            "аптек",
            "офис",
            "склад",
        ],
    },
    "home": {
        "queries": [
            "лофт для дня рождения",
            "антикафе для компании",
            "тайм-кафе для праздника",
            "пространство для вечеринки",
            "детский центр для праздника",
        ],
        "required": [
            "лофт",
            "антикафе",
            "тайм-кафе",
            "пространство",
            "студия",
            "детский центр",
            "игровая",
            "коттедж",
            "дом",
            "клуб",
        ],
        "forbidden": [
            "автомастер",
            "автосервис",
            "шиномонтаж",
            "гостиниц",
            "отель",
            "аптек",
            "клиник",
            "офис",
            "склад",
        ],
    },
    "mixed": {
        "queries": [
            "ресторан для дня рождения",
            "лофт для вечеринки",
            "банкетный зал",
            "загородный клуб для праздника",
        ],
        "required": [
            "ресторан",
            "кафе",
            "банкет",
            "лофт",
            "бар",
            "караоке",
            "загород",
            "база отдыха",
            "парк",
            "пространство",
        ],
        "forbidden": [
            "автомастер",
            "автосервис",
            "шиномонтаж",
            "аптек",
            "клиник",
            "офис",
            "склад",
        ],
    },
}

GENERIC_TOKENS = {
    "уютно",
    "красиво",
    "атмосферно",
    "стильно",
    "весело",
    "день рождения",
    "праздник",
    "компания",
    "друзья",
    "гости",
    "неплохо",
    "хорошо",
    "классно",
}

CITY_PATTERNS = [
    r"\bв\s+([А-ЯA-Z][а-яa-z\-]+)\b",
    r"\bгород\s+([А-ЯA-Z][а-яa-z\-]+)\b",
    r"\b([А-ЯA-Z][а-яa-z\-]+)\s+(?:центр|район)\b",
]


@dataclass
class SimpleProfile:
    title: str | None
    date: str | None
    budget: int | None
    guests_count: int | None
    format: str | None
    notes: str | None
    city: str | None
    latest_user_text: str | None


@dataclass
class SearchBrief:
    city: str | None
    summary: str
    queries: list[str]
    must_match: list[str]
    avoid: list[str]


@dataclass
class RankedVenue:
    score: float
    venue: VenueRecommendationOut


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _normalize_format(value: str | None) -> str:
    v = _normalize_text(value)
    if not v:
        return "mixed"

    mapping = {
        "дом": "home",
        "дома": "home",
        "домашний": "home",
        "квартира": "home",
        "коттедж": "home",

        "ресторан": "restaurant",
        "кафе": "restaurant",
        "банкет": "restaurant",
        "банкетный зал": "restaurant",
        "лофт": "restaurant",
        "караоке": "restaurant",
        "бар": "restaurant",

        "природа": "outdoor",
        "на природе": "outdoor",
        "улица": "outdoor",
        "парк": "outdoor",
        "загород": "outdoor",
        "база отдыха": "outdoor",
        "глэмпинг": "outdoor",
        "пикник": "outdoor",
        "шашлыки": "outdoor",
        "барбекю": "outdoor",

        "смешанный": "mixed",
        "home": "home",
        "restaurant": "restaurant",
        "outdoor": "outdoor",
        "mixed": "mixed",
    }

    if v in mapping:
        return mapping[v]

    if any(token in v for token in ["пикник", "шашлык", "барбекю", "природ", "парк", "загород", "база отдыха", "глэмпинг"]):
        return "outdoor"
    if any(token in v for token in ["ресторан", "кафе", "лофт", "банкет", "караоке", "бар"]):
        return "restaurant"
    if any(token in v for token in ["дом", "квартир", "коттедж", "антикафе", "пространство"]):
        return "home"

    return "mixed"

def _resolve_effective_format(event_format: str | None, *context_parts: str | None) -> str:
    context = " ".join(part for part in context_parts if part).strip()
    context_format = _normalize_format(context) if context else "mixed"

    # если в пожеланиях явно есть outdoor-сигнал, даём ему приоритет
    if context_format == "outdoor":
        return "outdoor"

    base_format = _normalize_format(event_format)

    # если поле события пустое/размытое, берём формат из контекста
    if base_format == "mixed" and context_format != "mixed":
        return context_format

    return base_format

def _extract_city(*parts: str | None) -> str | None:
    text = " ".join(part for part in parts if part).strip()
    if not text:
        return None
    for pattern in CITY_PATTERNS:
        match = re.search(pattern, text)
        if match:
            city = match.group(1).strip(" ,.;:")
            if len(city) >= 3:
                return city
    return None


def _collect_profile(event: Event, history: list[str], city_override: str | None, current_user: User | None = None) -> SimpleProfile:
    notes = getattr(event, "notes", None)
    latest_user_text = " ".join(history[-3:]) if history else None
    city = city_override or getattr(event, "city", None) or getattr(current_user, "region", None) or _extract_city(notes, " ".join(history[-4:]))

    effective_format = _resolve_effective_format(
        getattr(event, "format", None),
        notes,
        latest_user_text,
        getattr(event, "title", None),
    )

    return SimpleProfile(
        title=getattr(event, "title", None),
        date=str(getattr(event, "event_date", None) or "") or None,
        budget=getattr(event, "budget", None),
        guests_count=getattr(event, "guests_count", None),
        format=effective_format,
        notes=notes,
        city=city,
        latest_user_text=latest_user_text,
    )


def _compact_history(db: Session, event_id: int, limit: int = 12) -> list[str]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.event_id == event_id, ChatMessage.role == "user")
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return [row.content for row in reversed(rows)]


def _budget_label(profile: SimpleProfile) -> str:
    if profile.budget is None:
        return "бюджет не указан"
    if profile.guests_count and profile.guests_count > 0:
        per_guest = round(profile.budget / profile.guests_count)
        return f"общий бюджет ~{profile.budget} ₽, ориентир ~{per_guest} ₽ на гостя"
    return f"общий бюджет ~{profile.budget} ₽"


def _price_hint(profile: SimpleProfile) -> str | None:
    if profile.budget is None:
        return None
    if profile.guests_count and profile.guests_count > 0:
        per_guest = round(profile.budget / profile.guests_count)
        return f"Ориентир по бюджету: ~{per_guest} ₽/гость"
    return f"Ориентир по бюджету: до {profile.budget} ₽"


def _format_label(profile: SimpleProfile) -> str:
    return {
        "home": "домашний формат / пространство",
        "restaurant": "ресторан / кафе / лофт",
        "outdoor": "выездной / уличный формат",
        "mixed": "смешанный формат",
    }.get(profile.format, "смешанный формат")


def _rules_for_format(profile: SimpleProfile) -> dict[str, list[str]]:
    return FORMAT_RULES.get(profile.format or "mixed", FORMAT_RULES["mixed"])


def _budget_hint_token(profile: SimpleProfile) -> str:
    if profile.budget is None or not profile.guests_count:
        return ""
    per_guest = profile.budget / max(profile.guests_count, 1)
    if per_guest <= 1800:
        return "недорого"
    if per_guest >= 4500:
        return "премиум"
    return ""


def _keyword_candidates(*parts: str | None) -> list[str]:
    text = " ".join(part for part in parts if part)
    if not text:
        return []
    chunks = re.split(r"[,.;\n]| и | с | без ", text)
    result: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        value = _normalize_text(chunk)
        value = re.sub(r"[^\wа-яё\- ]+", "", value).strip()
        if len(value) < 4 or value in GENERIC_TOKENS:
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result[:8]


def _build_search_brief(profile: SimpleProfile, history: list[str], city_override: str | None) -> SearchBrief:
    rules = _rules_for_format(profile)
    ranked_keywords = _keyword_candidates(profile.notes, profile.latest_user_text)
    budget_hint = _budget_hint_token(profile)
    query_suffix = f" {budget_hint}" if budget_hint else ""
    queries = [f"{q}{query_suffix}".strip() for q in rules["queries"][:4]]
    avoid = [k for k in _keyword_candidates(" ".join(history[-4:])) if k.startswith("без ")]
    summary = (
        f"Подбор строится по данным события: {_format_label(profile)}, {_budget_label(profile)}."
        + (f" Пожелания: {', '.join(ranked_keywords[:4])}." if ranked_keywords else "")
    )
    return SearchBrief(
        city=city_override or profile.city,
        summary=summary,
        queries=queries,
        must_match=ranked_keywords[:5],
        avoid=avoid[:5],
    )


class DgisPlacesClient:
    def __init__(self) -> None:
        self.api_key = settings.DGIS_API_KEY
        self.base_url = settings.DGIS_BASE_URL
        self.timeout = settings.DGIS_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, *, city: str, query: str, limit: int) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        params: dict[str, Any] = {
            "q": f"{city} {query}".strip(),
            "type": "branch",
            "sort": "relevance",
            "search_type": "discovery_partial_searcher_strict",
            "search_is_query_text_complete": "true",
            "page_size": max(6, min(limit, 15)),
            "key": self.api_key,
            "fields": ",".join(
                [
                    "items.point",
                    "items.full_address_name",
                    "items.address",
                    "items.rubrics",
                    "items.reviews",
                    "items.schedule",
                    "items.flags",
                    "items.org",
                    "items.brand",
                ]
            ),
        }
        response = requests.get(self.base_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("result", {}).get("items", [])
        return items if isinstance(items, list) else []


def _item_name(item: dict[str, Any]) -> str:
    return (
        str(item.get("name") or "").strip()
        or str(item.get("org", {}).get("name") or "").strip()
        or str(item.get("brand", {}).get("name") or "").strip()
        or "Без названия"
    )


def _item_address(item: dict[str, Any]) -> str | None:
    address = item.get("full_address_name") or item.get("address_name")
    if address:
        return str(address)
    address_obj = item.get("address")
    if isinstance(address_obj, dict):
        for key in ("name", "address_name", "full_name", "comment"):
            value = address_obj.get(key)
            if value:
                return str(value)
    return None


def _item_rating(item: dict[str, Any]) -> tuple[float | None, int | None]:
    reviews = item.get("reviews") or {}
    rating_raw = reviews.get("rating") or reviews.get("general_rating") or reviews.get("org_rating")
    review_count_raw = (
        reviews.get("review_count")
        or reviews.get("general_review_count")
        or reviews.get("org_review_count")
    )
    rating: float | None = None
    review_count: int | None = None
    try:
        if rating_raw is not None:
            rating = float(str(rating_raw).replace(",", "."))
    except Exception:
        rating = None
    try:
        if review_count_raw is not None:
            review_count = int(float(str(review_count_raw).replace(",", ".")))
    except Exception:
        review_count = None
    return rating, review_count


def _item_text(item: dict[str, Any]) -> str:
    name = _item_name(item)
    address = _item_address(item) or ""
    rubrics = " ".join(str((rubric or {}).get("name") or "") for rubric in item.get("rubrics") or [])
    return re.sub(r"\s+", " ", f"{name} {address} {rubrics}".lower()).strip()


def _item_tags(item: dict[str, Any], profile: SimpleProfile, brief: SearchBrief) -> list[str]:
    tags: list[str] = []
    for rubric in (item.get("rubrics") or [])[:3]:
        name = str((rubric or {}).get("name") or "").strip()
        if name:
            tags.append(name)
    existing = {tag.lower() for tag in tags}
    for keyword in brief.must_match[:3]:
        low = keyword.lower().strip()
        if low and low not in existing:
            tags.append(keyword)
            existing.add(low)
    if profile.guests_count:
        tags.append(f"~{profile.guests_count} гостей")
    return tags[:4]


def _passes_format_guard(item: dict[str, Any], profile: SimpleProfile) -> bool:
    item_text = _item_text(item)
    rules = _rules_for_format(profile)
    if any(token in item_text for token in rules["forbidden"]):
        return False
    return any(token in item_text for token in rules["required"])


def _score_candidate(
    item: dict[str, Any],
    *,
    query: str,
    profile: SimpleProfile,
    position: int,
    must_match: list[str],
    avoid: list[str],
) -> tuple[float, str]:
    rating, review_count = _item_rating(item)
    item_text = _item_text(item)
    rules = _rules_for_format(profile)
    score = max(0.0, 65.0 - position * 3.0)
    if rating is not None:
        score += rating * 8
    if review_count is not None:
        score += min(review_count, 300) / 15

    category_hits = [token for token in rules["required"] if token in item_text]
    if category_hits:
        score += 18

    matched_keywords: list[str] = []
    for keyword in must_match[:6]:
        if keyword and keyword in item_text:
            score += 9
            matched_keywords.append(keyword)

    for keyword in avoid[:5]:
        if keyword and keyword in item_text:
            score -= 14

    if profile.guests_count is not None:
        score += min(profile.guests_count, 20) / 3

    reason_parts: list[str] = []
    if category_hits:
        reason_parts.append("совпадает по типу места")
    if matched_keywords:
        reason_parts.append("совпали пожелания: " + ", ".join(matched_keywords[:3]))
    if profile.guests_count is not None:
        reason_parts.append(f"подходит для компании около {profile.guests_count} гостей")
    if rating is not None:
        if review_count is not None:
            reason_parts.append(f"рейтинг {rating:.1f} на основе {review_count} отзывов")
        else:
            reason_parts.append(f"рейтинг {rating:.1f}")
    if not reason_parts:
        reason_parts.append(f"выдача 2GIS по запросу «{query}»")
    return score, ". ".join(reason_parts).capitalize() + "."


def get_event_recommendations(
    *,
    event: Event,
    current_user: User,
    db: Session,
    city_override: str | None = None,
    limit: int = 6,
) -> VenueRecommendationsOut:
    history = _compact_history(db, event.id)
    profile = _collect_profile(event=event, history=history, city_override=city_override, current_user=current_user)
    brief = _build_search_brief(profile=profile, history=history, city_override=city_override)
    provider = "2gis"
    warnings: list[str] = []
    missing_fields: list[str] = []

    if not brief.city:
        missing_fields.append("city")
        return VenueRecommendationsOut(
            items=[],
            meta=RecommendationMetaOut(
                city=None,
                provider=provider,
                generated_summary=brief.summary,
                search_queries=brief.queries,
                missing_fields=missing_fields,
                warnings=["Укажи город или напиши его в пожеланиях, чтобы искать реальные заведения по карте."],
            ),
        )

    client = DgisPlacesClient()
    if not client.is_configured:
        warnings.append("Для реального списка заведений укажи DGIS_API_KEY в backend/.env.")
        return VenueRecommendationsOut(
            items=[],
            meta=RecommendationMetaOut(
                city=brief.city,
                provider="2gis_not_configured",
                generated_summary=brief.summary,
                search_queries=brief.queries,
                missing_fields=missing_fields,
                warnings=warnings,
            ),
        )

    ranked: dict[str, RankedVenue] = {}
    filtered_out_by_category = 0

    for query_index, query in enumerate(brief.queries[:4]):
        try:
            raw_items = client.search(city=brief.city, query=query, limit=max(limit, 10))
        except Exception as exc:
            warnings.append(f'Не удалось выполнить запрос "{query}": {type(exc).__name__}.')
            continue

        for position, item in enumerate(raw_items, start=1):
            if not _passes_format_guard(item, profile):
                filtered_out_by_category += 1
                continue

            name = _item_name(item)
            address = _item_address(item)
            rating, review_count = _item_rating(item)
            score, reason = _score_candidate(
                item,
                query=query,
                profile=profile,
                position=position + query_index * 2,
                must_match=brief.must_match,
                avoid=brief.avoid,
            )
            key = str(item.get("id") or f"{name}|{address}")
            venue = VenueRecommendationOut(
                id=key,
                name=name,
                address=address,
                rating=rating,
                review_count=review_count,
                price_note=_price_hint(profile),
                source_query=query,
                reason=reason,
                source="2gis",
                tags=_item_tags(item, profile, brief),
                yandex_maps_url=yandex_maps_search_url(" ".join(part for part in [name, address or brief.city] if part)),
                two_gis_url=two_gis_search_url(" ".join(part for part in [name, address or brief.city] if part)),
            )
            existing = ranked.get(key)
            if existing is None or score > existing.score:
                ranked[key] = RankedVenue(score=score, venue=venue)

    ordered = [item.venue for item in sorted(ranked.values(), key=lambda x: x.score, reverse=True)[:limit]]
    if filtered_out_by_category:
        warnings.append(f"Отфильтровано нерелевантных мест: {filtered_out_by_category}.")
    if not ordered:
        warnings.append(
            "2GIS не вернул подходящие заведения нужного типа. Попробуй уточнить формат, город или добавить больше пожеланий в чат."
        )

    return VenueRecommendationsOut(
        items=ordered,
        meta=RecommendationMetaOut(
            city=brief.city,
            provider=provider,
            generated_summary=brief.summary,
            search_queries=brief.queries,
            missing_fields=missing_fields,
            warnings=warnings,
        ),
    )
