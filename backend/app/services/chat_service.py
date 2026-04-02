import re
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from gigachat.exceptions import RateLimitError

from app.core.config import settings
from app.models.chat import ChatMessage
from app.models.event import Event
from app.models.wishlist import Wishlist
from app.schemas.chat import ChatActionOut, ChatMessageOut
from app.services.gigachat_client import make_client


TOPIC_ACTIONS: dict[str, list[dict[str, str]]] = {
    "places": [
        {"id": "open-places", "label": "Открыть места", "kind": "open_tab", "target_tab": "places"},
        {"id": "more-places", "label": "Подобрать ещё", "kind": "send_prompt", "prompt": "Подбери ещё 2–3 варианта для этой идеи."},
        {"id": "cheaper-places", "label": "Сделать дешевле", "kind": "send_prompt", "prompt": "Сделай этот вариант дешевле и сохрани атмосферу."},
        {"id": "backup-places", "label": "План Б", "kind": "send_prompt", "prompt": "Предложи запасной вариант на случай плохой погоды или отмены площадки."},
    ],
    "gifts": [
        {"id": "open-gifts", "label": "Открыть подарки", "kind": "open_tab", "target_tab": "gifts"},
        {"id": "more-gifts", "label": "Подобрать ещё", "kind": "send_prompt", "prompt": "Подбери ещё 3 идеи подарка в похожем стиле."},
        {"id": "cheaper-gifts", "label": "Дешевле", "kind": "send_prompt", "prompt": "Сделай подборку дешевле, но не слишком банальной."},
        {"id": "save-gifts", "label": "Добавить в подарки", "kind": "send_prompt", "prompt": "Сохрани эти идеи в раздел подарков и предложи ещё один запасной вариант."},
    ],
    "guests": [
        {"id": "open-guests", "label": "Открыть гостей", "kind": "open_tab", "target_tab": "guests"},
        {"id": "invite-text", "label": "Текст приглашения", "kind": "send_prompt", "prompt": "Подготовь короткий текст приглашения для гостей."},
        {"id": "warmer-invite", "label": "Сделать теплее", "kind": "send_prompt", "prompt": "Сделай приглашение более тёплым и дружелюбным."},
        {"id": "shorter-list", "label": "Сократить список", "kind": "send_prompt", "prompt": "Помоги сократить список гостей без неловкости."},
    ],
    "backup": [
        {"id": "open-backup", "label": "Открыть план Б", "kind": "open_tab", "target_tab": "backup"},
        {"id": "indoor-backup", "label": "В помещении", "kind": "send_prompt", "prompt": "Подбери запасной вариант в помещении."},
        {"id": "cheaper-backup", "label": "Сделать дешевле", "kind": "send_prompt", "prompt": "Сделай запасной вариант дешевле."},
        {"id": "more-backup", "label": "Ещё вариант", "kind": "send_prompt", "prompt": "Предложи ещё один запасной сценарий."},
    ],
    "overview": [
        {"id": "open-overview", "label": "Открыть обзор", "kind": "open_tab", "target_tab": "overview"},
        {"id": "clarify-format", "label": "Уточнить формат", "kind": "send_prompt", "prompt": "Задай 2–3 уточняющих вопроса по формату праздника."},
        {"id": "cheaper-overview", "label": "Сделать дешевле", "kind": "send_prompt", "prompt": "Сократи бюджет и предложи обновлённую идею."},
        {"id": "more-ideas", "label": "Ещё идеи", "kind": "send_prompt", "prompt": "Предложи ещё 2–3 идеи в том же стиле."},
    ],
}

RUS_MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}

CHANGE_HINTS = (
    "измени",
    "поменя",
    "обнови",
    "перенес",
    "перенеси",
    "сделай",
    "поставь",
    "пусть будет",
    "давай",
    "хочу поменять",
    "хочу изменить",
)

SAVE_HINTS = ("добав", "сохран", "запиш", "внес", "закин", "полож")
GIFT_HINTS = ("подар", "вишлист", "wishlist")

GIFT_LINE_SKIP_PREFIXES = (
    "варианты",
    "следующий шаг",
    "что можно поменять",
    "что уточнить",
    "как реализовать",
    "преимущества",
    "недостатки",
    "otmech.ai",
    "подобрал",
    "сохранил",
    "можно",
    "почему подходит",
)


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
        "Используй эти данные в ответах. Если пользователь просит поменять формат, дату, бюджет, город или количество гостей, учитывай уже обновлённые значения и опирайся на них в следующем шаге. "
        "Если пользователь просит добавить подарки в список, учитывай текущий вишлист и не дублируй его."
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты — ИИ-агент по организации дня рождения пользователя. "
                "Веди его по сценарию: уточни формат, предложи основу праздника, помоги с выбором места или домашнего сценария, затем с приглашениями и запасным планом. "
                "Если пользователь отказывается от предложенных вариантов или меняет направление, адаптируй сценарий и кратко объясни следующий шаг. "
                "Отвечай на русском языке, кратко и практично. "
                "Обычно используй компактный шаблон: короткий заголовок или первая фраза, затем 2–4 коротких пункта и один следующий шаг. "
                "Не имитируй кнопки в тексте, не пиши 'Действия:' и не вставляй квадратные скобки с командами — интерфейс показывает действия отдельно. "
                "Если предлагаешь варианты — давай не больше 3 коротких вариантов. "
                "Не пиши длинные вступления, длинные абзацы и повторы. "
                "Если пользователь только что изменил параметры события, явно опирайся на новые значения, а не на старые."
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


def _normalize(text: str | None) -> str:
    return (text or "").strip().lower()


def _has_change_intent(text: str) -> bool:
    low = _normalize(text)
    return any(hint in low for hint in CHANGE_HINTS)


def _parse_number_fragment(raw: str) -> int | None:
    cleaned = raw.lower().replace("₽", " ")
    multiplier = 1
    if re.search(r"\b(?:к|тыс|тысяч)\b", cleaned):
        multiplier = 1000
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None
    value = int(digits)
    if multiplier == 1000 and value < 1000:
        value *= 1000
    return value


def _extract_budget(text: str) -> int | None:
    low = _normalize(text)
    if "бюдж" not in low:
        return None

    patterns = [
        r"бюдж\w*[^\d]{0,12}(\d[\d\s]{0,12}(?:\s*(?:к|тыс|тысяч))?)",
        r"до\s*(\d[\d\s]{0,12}(?:\s*(?:к|тыс|тысяч))?)\s*(?:₽|руб|р)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, low)
        if not match:
            continue
        value = _parse_number_fragment(match.group(1))
        if value is not None:
            return value
    return None


def _extract_guest_count(text: str) -> int | None:
    low = _normalize(text)
    if not any(word in low for word in ("гост", "человек")):
        return None

    patterns = [
        r"(?:гост(?:ей|я)?|человек)[^\d]{0,8}(\d{1,3})",
        r"на\s*(\d{1,3})\s*человек",
    ]
    for pattern in patterns:
        match = re.search(pattern, low)
        if match:
            return int(match.group(1))
    return None


def _extract_city(text: str) -> str | None:
    match = re.search(r"(?:город|в городе)\s+([A-Za-zА-Яа-яЁё\- ]{2,40})", text, flags=re.IGNORECASE)
    if not match:
        return None
    city = match.group(1).strip(" .,;:")
    if not city:
        return None
    return city[:80]


def _extract_relative_date(text: str) -> date | None:
    low = _normalize(text)
    today = date.today()
    if "послезавтра" in low:
        return today + timedelta(days=2)
    if "завтра" in low:
        return today + timedelta(days=1)
    if "сегодня" in low:
        return today
    return None


def _extract_date(text: str) -> date | None:
    relative = _extract_relative_date(text)
    if relative is not None:
        return relative

    iso = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", text)
    if iso:
        year, month, day = map(int, iso.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None

    dotted = re.search(r"(\d{1,2})\.(\d{1,2})\.(20\d{2})", text)
    if dotted:
        day, month, year = map(int, dotted.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None

    dotted_short = re.search(r"(\d{1,2})\.(\d{1,2})(?!\.\d)", text)
    if dotted_short and ("дата" in _normalize(text) or _has_change_intent(text)):
        day, month = map(int, dotted_short.groups())
        year = date.today().year
        try:
            return date(year, month, day)
        except ValueError:
            return None

    month_name = re.search(
        r"(\d{1,2})\s+(январ[ьяе]?|феврал[ьяе]?|март[ае]?|апрел[ьяе]?|ма[йяе]?|июн[ьяе]?|июл[ьяе]?|август[ае]?|сентябр[ьяе]?|октябр[ьяе]?|ноябр[ьяе]?|декабр[ьяе]?)(?:\s+(20\d{2}))?",
        text,
        flags=re.IGNORECASE,
    )
    if month_name:
        day = int(month_name.group(1))
        month_token = month_name.group(2).lower()
        month = next((value for key, value in RUS_MONTHS.items() if month_token.startswith(key)), None)
        year = int(month_name.group(3)) if month_name.group(3) else date.today().year
        if month is not None:
            try:
                return date(year, month, day)
            except ValueError:
                return None

    return None


def _extract_format_updates(text: str) -> dict[str, str | None]:
    low = _normalize(text)
    updates: dict[str, str | None] = {}

    if any(word in low for word in ("домаш", "дома", "квартир")):
        updates["format"] = "home"
        updates["venue_mode"] = "home"
        return updates

    if any(word in low for word in ("смешан", "mixed")):
        updates["format"] = "mixed"
        updates["venue_mode"] = "undecided"
        return updates

    if any(word in low for word in ("ресторан", "кафе", "террас", "антикафе", "банкет")):
        updates["format"] = "restaurant"
        updates["venue_mode"] = "outside"
        return updates

    if any(word in low for word in ("пикник", "на природе", "в парке", "на улице", "пляж", "лес")):
        updates["venue_mode"] = "outside"
        return updates

    return updates


def _apply_event_updates_from_text(event: Event, user_text: str, db: Session) -> list[str]:
    low = _normalize(user_text)
    wants_change = _has_change_intent(user_text)
    changes: list[str] = []
    updated = False

    if wants_change or "бюдж" in low:
        budget = _extract_budget(user_text)
        if budget is not None and budget != event.budget:
            event.budget = budget
            updated = True
            changes.append(f"бюджет — {budget:,} ₽".replace(",", " "))

    if wants_change or "дат" in low or "перенес" in low:
        new_date = _extract_date(user_text)
        if new_date is not None and new_date != event.event_date:
            event.event_date = new_date
            updated = True
            changes.append(f"дата — {new_date.isoformat()}")

    if wants_change or "формат" in low or "режим" in low or "место проведения" in low:
        format_updates = _extract_format_updates(user_text)
        for key, value in format_updates.items():
            if getattr(event, key) != value:
                setattr(event, key, value)
                updated = True
                if key == "format" and value:
                    changes.append(f"формат — {value}")
                elif key == "venue_mode" and value:
                    changes.append(f"режим площадки — {value}")

    if wants_change or "гост" in low or "человек" in low:
        guests_count = _extract_guest_count(user_text)
        if guests_count is not None and guests_count != event.guests_count:
            event.guests_count = guests_count
            updated = True
            changes.append(f"гостей — {guests_count}")

    if wants_change or "город" in low:
        city = _extract_city(user_text)
        if city and city != event.city:
            event.city = city
            updated = True
            changes.append(f"город — {city}")

    if updated:
        db.add(event)
        db.commit()
        db.refresh(event)

    return changes


def _find_topic(text: str, event: Event) -> str:
    low = _normalize(text)
    if any(word in low for word in ("подар", "вишлист", "wishlist", "сувенир", "именин")):
        return "gifts"
    if any(word in low for word in ("гост", "приглаш", "приглашен", "список гостей", "rsvp")):
        return "guests"
    if any(word in low for word in ("план б", "запасн", "дожд", "непогод", "в помещении")):
        return "backup"
    if any(
        word in low
        for word in (
            "мест",
            "локац",
            "площад",
            "ресторан",
            "кафе",
            "пикник",
            "террас",
            "пляж",
            "лес",
            "дома",
            "на улице",
        )
    ):
        return "places"
    if getattr(event, "venue_mode", None) in {"outside", "home"}:
        return "places"
    return "overview"


def _extract_variant_numbers(text: str) -> list[int]:
    numbers: list[int] = []
    seen: set[int] = set()

    for match in re.finditer(r"вариант\s*([1-3])", text, flags=re.IGNORECASE):
        number = int(match.group(1))
        if number not in seen:
            seen.add(number)
            numbers.append(number)

    if not numbers:
        listed = re.findall(r"^\s*(?:\*\*)?([1-3])(?:\*\*)?[\.)]", text, flags=re.MULTILINE)
        if 2 <= len(listed) <= 3:
            for item in listed:
                number = int(item)
                if number not in seen:
                    seen.add(number)
                    numbers.append(number)

    return numbers[:3]


def _make_action(data: dict[str, str]) -> ChatActionOut:
    return ChatActionOut(
        id=data["id"],
        label=data["label"],
        kind=data.get("kind", "send_prompt"),
        prompt=data.get("prompt"),
        target_tab=data.get("target_tab"),
    )


def _iter_topic_actions(topic: str) -> Iterable[ChatActionOut]:
    for action in TOPIC_ACTIONS.get(topic, TOPIC_ACTIONS["overview"]):
        yield _make_action(action)


def build_chat_actions(event: Event, content: str) -> list[ChatActionOut]:
    if not content.strip():
        return []

    topic = _find_topic(content, event)
    actions: list[ChatActionOut] = []
    used_ids: set[str] = set()

    for number in _extract_variant_numbers(content):
        action = ChatActionOut(
            id=f"pick-{topic}-{number}",
            label=f"Выбрать {number}",
            kind="send_prompt",
            prompt=f"Выбираю вариант {number}. Сохрани его как основу и подскажи следующий шаг.",
        )
        actions.append(action)
        used_ids.add(action.id)

    for action in _iter_topic_actions(topic):
        if action.id in used_ids:
            continue
        actions.append(action)
        used_ids.add(action.id)
        if len(actions) >= 4:
            break

    return actions[:4]


def serialize_chat_message(message: ChatMessage, event: Event) -> ChatMessageOut:
    actions = build_chat_actions(event, message.content) if message.role == "assistant" else []
    return ChatMessageOut(
        id=message.id,
        event_id=message.event_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        actions=actions,
    )


def _wants_save_gifts(user_text: str) -> bool:
    low = _normalize(user_text)
    if any(hint in low for hint in GIFT_HINTS) and any(hint in low for hint in SAVE_HINTS):
        return True
    return low in {
        "добавь",
        "да, добавь",
        "да добавь",
        "добавь это",
        "добавь их",
        "сохрани",
        "сохрани это",
        "запиши это",
    }


def _clean_markdown_line(text: str) -> str:
    line = text.strip()
    line = re.sub(r"^[#>\s]+", "", line)
    line = re.sub(r"[*_`]+", "", line)
    line = line.strip()
    return line


def _extract_gift_suggestions(content: str) -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    for raw_line in content.splitlines():
        line = _clean_markdown_line(raw_line)
        if not line:
            continue

        line = re.sub(r"^(?:[-•–]\s*)", "", line)
        line = re.sub(r"(?i)^вариант\s*\d+\s*[:.-]\s*", "", line)
        line = re.sub(r"^\d+[\).]\s*", "", line)
        line = line.strip(" -–—")
        if not line:
            continue

        low = line.lower()
        if any(low.startswith(prefix) for prefix in GIFT_LINE_SKIP_PREFIXES):
            continue

        title = line
        description: str | None = None
        for separator in (" — ", " – ", " - ", ": "):
            if separator not in line:
                continue
            left, right = line.split(separator, 1)
            left = left.strip()
            right = right.strip()
            if 1 <= len(left.split()) <= 8 and len(right) >= 4:
                title = left
                description = right
                break

        if len(title.split()) > 8 or len(title) > 90:
            continue

        if any(token in title.lower() for token in ("следующий шаг", "план б", "приглашение", "сценарий")):
            continue

        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append((title, description))
        if len(items) >= 5:
            break

    return items


def _save_gift_suggestions(event: Event, content: str, db: Session) -> int:
    suggestions = _extract_gift_suggestions(content)
    if not suggestions:
        return 0

    existing = {
        (item.title or "").strip().lower()
        for item in db.query(Wishlist).filter(Wishlist.event_id == event.id).all()
    }

    created = 0
    for title, description in suggestions:
        key = title.strip().lower()
        if not key or key in existing:
            continue
        db.add(
            Wishlist(
                event_id=event.id,
                title=title.strip(),
                description=description,
                priority="medium",
                status="active",
            )
        )
        existing.add(key)
        created += 1

    if created:
        db.commit()

    return created


def _save_gifts_from_last_assistant(event: Event, db: Session) -> int:
    last_assistant = (
        db.query(ChatMessage)
        .filter(ChatMessage.event_id == event.id, ChatMessage.role == "assistant")
        .order_by(ChatMessage.id.desc())
        .first()
    )
    if not last_assistant:
        return 0
    return _save_gift_suggestions(event, last_assistant.content, db)


def ask_gigachat(event: Event, user_text: str, db: Session) -> tuple[ChatMessage, ChatMessage]:
    applied_changes = _apply_event_updates_from_text(event, user_text, db)
    saved_from_previous = _save_gifts_from_last_assistant(event, db) if _wants_save_gifts(user_text) else 0

    user_msg = ChatMessage(event_id=event.id, role="user", content=user_text)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    messages = build_messages(event, db)

    try:
        with make_client() as giga:
            response = giga.chat(
                {
                    "model": settings.GIGACHAT_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                }
            )
        assistant_text = response.choices[0].message.content or ""
    except RateLimitError:
        assistant_text = "Извините, сейчас слишком много запросов к ИИ. Пожалуйста, подождите минуту и попробуйте снова."
    except Exception as e:
        assistant_text = f"Произошла ошибка при обращении к ИИ: {str(e)}"

    saved_from_current = 0
    if _wants_save_gifts(user_text) and saved_from_previous == 0:
        saved_from_current = _save_gift_suggestions(event, assistant_text, db)

    notes: list[str] = []
    if applied_changes:
        notes.append("Обновил параметры события: " + ", ".join(applied_changes) + ".")
    saved_total = saved_from_previous + saved_from_current
    if saved_total:
        notes.append(f"Сохранил идеи в подарки: {saved_total} шт.")
    if notes:
        assistant_text = "✅ " + " ".join(notes) + "\n\n" + assistant_text

    assistant_msg = ChatMessage(event_id=event.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return user_msg, assistant_msg
