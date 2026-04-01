import re
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatMessage
from app.models.event import Event
from app.models.wishlist import Wishlist
from app.services.gigachat_client import make_client

import json

WISHLIST_TRIGGER_PATTERNS = (
    r"\bдобав(?:ь|ить|ь-ка|ьте)\b",
    r"\bсохрани(?:ть)?\b",
    r"\bзанеси\b",
    r"\bв\s+вишлист\b",
    r"\bв\s+список\b",
)

WISHLIST_BANNED_PARTS = (
    "вот обновл",
    "обновленный список",
    "обновлённый список",
    "список подар",
    "какой подарок",
    "какой из",
    "выберите",
    "выберете",
    "следующий шаг",
    "подобрал",
    "добавил",
    "могу добавить",
    "вариант",
    "приоритет",
    "действия",
    "что можно",
    "как реализовать",
    "преимущества",
    "недостатки",
)


def serialize_chat_message(message, event=None):
    actions = getattr(message, "actions", None)
    if isinstance(actions, str):
        try:
            actions = json.loads(actions)
        except Exception:
            actions = []
    if actions is None:
        actions = []

    payload = {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat() if getattr(message, "created_at", None) else None,
        "actions": actions,
    }

    if event is not None:
        payload["event_id"] = event.id

    return payload

def build_messages(event: Event, db: Session) -> list[dict]:
    wishlist_items = db.query(Wishlist).filter(Wishlist.event_id == event.id).all()
    wishlist_text = ""
    if wishlist_items:
        wishlist_text = "\nСписок желаемых подарков:\n"
        for item in wishlist_items:
            wishlist_text += f"- {item.title}"
            if item.description:
                wishlist_text += f": {item.description}"
            if item.price:
                wishlist_text += f" (цена: {item.price} руб.)"
            if item.url:
                wishlist_text += " [ссылка]"
            wishlist_text += "\n"
    else:
        wishlist_text = "\nСписок желаемых подарков: пока пуст\n"

    event_context = (
        f"Данные о событии:\n"
        f"- Название: {event.title}\n"
        f"- Дата: {event.event_date or 'не указана'}\n"
        f"- Бюджет: {event.budget or 'не указан'}\n"
        f"- Количество гостей: {event.guests_count or 'не указано'}\n"
        f"- Формат: {event.format or 'не указан'}\n"
        f"- Режим площадки: {getattr(event, 'venue_mode', None) or 'не указан'}\n"
        f"- Город: {getattr(event, 'city', None) or 'не указан'}\n"
        f"- Выбранная основа: {getattr(event, 'selected_option', None) or 'не выбрана'}\n"
        f"- Пожелания: {event.notes or 'нет'}\n"
        f"{wishlist_text}\n\n"
        "Используй эти данные в ответах. Если пользователь меняет формат, бюджет или тип площадки, явно учитывай это и предлагай следующий практический шаг. "
        "Если пользователь просит добавить подарки в вишлист, сначала коротко подтверди, а затем перечисли сами подарки отдельными пунктами списка без лишних заголовков внутри списка. "
        "Не добавляй в список служебные фразы вроде 'вот обновлённый список', 'следующий шаг', 'какой подарок выберете'."
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты — ИИ-агент по организации дня рождения пользователя. "
                "Веди его по сценарию: уточни формат, предложи основу праздника, помоги с выбором места или домашнего сценария, затем с приглашениями и запасным планом. "
                "Если пользователь отказывается от предложенных вариантов или меняет направление, адаптируй сценарий и кратко объясни следующий шаг. "
                "Отвечай на русском языке, очень кратко и практично. "
                "Обычно давай 2–4 короткие строки или список максимум из 3 пунктов. "
                "Не пиши длинные вступления, длинные абзацы и повторы. "
                "Если предлагаешь варианты — давай не больше 3 коротких вариантов. "
                "Если перечисляешь подарки для сохранения, перечисляй только реальные названия подарков отдельными пунктами. "
                "Завершай ответ одним следующим шагом."
            ),
        },
        {
            "role": "user",
            "content": event_context,
        },
    ]

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.event_id == event.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    for item in history:
        messages.append({"role": item.role, "content": item.content})

    return messages



def _normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())



def _user_requests_wishlist_add(user_text: str) -> bool:
    lowered = user_text.lower()
    if "подар" not in lowered and "вишлист" not in lowered and "список" not in lowered:
        return False
    return any(re.search(pattern, lowered) for pattern in WISHLIST_TRIGGER_PATTERNS)



def _clean_candidate_line(line: str) -> tuple[str, str | None] | None:
    text = line.strip()
    if not text:
        return None

    text = re.sub(r"^#{1,6}\s*", "", text)
    text = re.sub(r"^\*\*(.+?)\*\*$", r"\1", text)
    text = re.sub(r"^[-*•]\s+", "", text)
    text = re.sub(r"^\d+[.)]\s+", "", text)
    text = re.sub(r"^\*\*(\d+[.)]\s*)?(.+?)\*\*$", r"\2", text)
    text = text.strip(" -*•\t")

    lowered = text.lower()
    if not text or len(text) < 6:
        return None
    if text.endswith(":") or text.endswith("?"):
        return None
    if any(part in lowered for part in WISHLIST_BANNED_PARTS):
        return None
    if lowered.startswith(("приоритет", "действия", "шаг ", "сейчас ", "итог")):
        return None
    if text.count(" ") > 16:
        return None
    if not re.search(r"[а-яёa-z]", text, re.IGNORECASE):
        return None

    title = text
    description = None
    if " — " in text:
        left, right = text.split(" — ", 1)
        if left.strip() and right.strip():
            title, description = left.strip(), right.strip()
    elif ": " in text:
        left, right = text.split(": ", 1)
        if len(left.split()) <= 10 and right.strip():
            title, description = left.strip(), right.strip()

    if len(title) < 4:
        return None
    return title.rstrip("."), description



def _extract_wishlist_candidates(assistant_text: str) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()

    for raw_line in assistant_text.splitlines():
        parsed = _clean_candidate_line(raw_line)
        if not parsed:
            continue
        title, description = parsed
        normalized = _normalize_title(title)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(
            {
                "title": title,
                "description": description,
                "priority": "medium",
                "status": "active",
            }
        )
        if len(candidates) >= 5:
            break

    return candidates



def _save_wishlist_candidates(event: Event, db: Session, assistant_text: str) -> int:
    candidates = _extract_wishlist_candidates(assistant_text)
    if not candidates:
        return 0

    existing_titles = {
        _normalize_title(item.title)
        for item in db.query(Wishlist).filter(Wishlist.event_id == event.id).all()
    }

    created = 0
    for candidate in candidates:
        normalized = _normalize_title(candidate["title"])
        if normalized in existing_titles:
            continue
        db.add(Wishlist(event_id=event.id, **candidate))
        existing_titles.add(normalized)
        created += 1

    if created:
        db.commit()

    return created



def ask_gigachat(event: Event, user_text: str, db: Session) -> tuple[ChatMessage, ChatMessage]:
    user_msg = ChatMessage(event_id=event.id, role="user", content=user_text)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    messages = build_messages(event, db)

    with make_client() as giga:
        response = giga.chat(
            {
                "model": settings.GIGACHAT_MODEL,
                "messages": messages,
                "temperature": 0.7,
            }
        )

    assistant_text = response.choices[0].message.content

    if _user_requests_wishlist_add(user_text):
        created = _save_wishlist_candidates(event, db, assistant_text)
        if created:
            assistant_text = f"{assistant_text}\n\nДобавил в список подарков: {created}."

    assistant_msg = ChatMessage(event_id=event.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return user_msg, assistant_msg
