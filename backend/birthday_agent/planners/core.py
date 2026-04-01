from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from birthday_agent.llm.base import LLMClient
from birthday_agent.models import PlanDraft, TaskItem, UserProfile


def _iso(dt: Optional[datetime]) -> str:
    return dt.isoformat() if dt else ""


def build_plan_prompt(profile: UserProfile) -> str:
    profile_dict = json.loads(profile.model_dump_json())
    return (
        "Сформируй план дня рождения для пользователя. Требования:\n"
        "- Дай 2-3 концепции (коротко), затем выбери одну (наиболее подходящую) и оформи как итог.\n"
        "- Для итога: локации (3 идеи), меню (5-8 позиций), развлечения (5 идей), оформление (5 идей), подарки (7 идей).\n"
        "- Сформируй текст приглашения (дружелюбный, с местом для даты/времени/адреса).\n"
        "- Сформируй чек-лист задач с дедлайнами относительно даты (если даты нет — сделай относительные дедлайны: -14д, -7д, -2д, -0д).\n"
        "- В каждом элементе `checklist` поле `owner` должно быть ровно одним из: `agent` или `user`.\n"
        "- В каждом элементе `checklist` поле `priority` должно быть ровно одним из: `low`, `medium`, `high`.\n"
        "- Ответ верни в JSON строгой структуры:\n"
        "{\n"
        '  "concept_title": "...",\n'
        '  "concept_summary": "...",\n'
        '  "venue_ideas": ["..."],\n'
        '  "menu_ideas": ["..."],\n'
        '  "gift_ideas": ["..."],\n'
        '  "entertainment_ideas": ["..."],\n'
        '  "decor_ideas": ["..."],\n'
        '  "invitation_text": "...",\n'
        '  "checklist": [\n'
        '    {"id":"t1","title":"...","description":"...","due_at":"YYYY-MM-DDTHH:MM:SS","owner":"agent","priority":"medium"}\n'
        "  ]\n"
        "}\n\n"
        f"Профиль пользователя (JSON):\n{json.dumps(profile_dict, ensure_ascii=False, indent=2)}\n"
    )


def _fallback_plan(profile: UserProfile) -> PlanDraft:
    now = datetime.now()
    base_due = now + timedelta(days=14)
    tasks = [
        TaskItem(
            id="t1",
            title="Выбрать дату/время и формат",
            description="Уточнить дату, длительность и формат (дом/кафе/природа).",
            due_at=base_due - timedelta(days=10),
            owner="user",
            priority="high",
        ),
        TaskItem(
            id="t2",
            title="Составить список гостей и собрать контакты",
            description="Список гостей + каналы связи (Telegram/WhatsApp/VK).",
            due_at=base_due - timedelta(days=9),
            owner="user",
            priority="high",
        ),
        TaskItem(
            id="t3",
            title="Подобрать локацию и забронировать",
            description="2–3 варианта, затем бронь/подтверждение.",
            due_at=base_due - timedelta(days=7),
            owner="agent",
            priority="high",
        ),
        TaskItem(
            id="t4",
            title="Собрать меню и заказать доставку/продукты",
            description="Учесть ограничения и предпочтения.",
            due_at=base_due - timedelta(days=2),
            owner="agent",
            priority="high",
        ),
        TaskItem(
            id="t5",
            title="Разослать приглашения и собрать ответы",
            description="Текст приглашения + RSVP.",
            due_at=base_due - timedelta(days=7),
            owner="agent",
            priority="high",
        ),
    ]
    return PlanDraft(
        concept_title="Уютный вечер с активностью",
        concept_summary="Небольшая компания, вкусная еда, плейлист и интерактив (квиз/настолки).",
        venue_ideas=[
            f"Домашняя вечеринка в {profile.city or 'вашем городе'}",
            "Небольшое кафе рядом с домом/работой",
            "Лофт/антикафе на 3–5 часов",
        ],
        menu_ideas=[
            "Сырная тарелка + фрукты",
            "Закуски (брускетты/канапе)",
            "Салат (Цезарь/овощной)",
            "Горячее (паста/пицца/гриль)",
            "Торт или капкейки",
            "Безалкогольные напитки + чай/кофе",
        ],
        gift_ideas=[
            "Сертификат на впечатление (SPA/квест/мастер‑класс)",
            "Подарок по хобби (аксессуар/инструмент)",
            "Книга/подписка",
            "Качественный термос/бутылка",
            "Наушники/гаджет‑аксессуар",
            "Плед/уют для дома",
            "Совместный подарок: поездка на выходные",
        ],
        entertainment_ideas=[
            "Мини‑квиз про именинника",
            "Настолки (по вкусу компании)",
            "Плейлист + караоке дома/в лофте",
            "Фото‑челлендж на вечер",
            "Небольшой просмотр/викторина по любимому сериалу",
        ],
        decor_ideas=[
            "Гирлянда тёплого света",
            "2–3 акцентных цвета в шарах",
            "Свечи/аромадиффузор",
            "Небольшая фотозона (фон + реквизит)",
            "Именные карточки/наклейки (по желанию)",
        ],
        invitation_text=(
            "Привет! Приглашаю тебя на мой день рождения.\n"
            "Дата/время: [вставить]\n"
            "Место: [вставить]\n"
            "Формат: уютный вечер, немного еды и развлечений.\n"
            "Подтверди, пожалуйста, сможешь ли прийти (RSVP) до [дата]."
        ),
        checklist=tasks,
    )


def generate_plan(profile: UserProfile, llm: LLMClient) -> PlanDraft:
    prompt = build_plan_prompt(profile)
    resp = llm.complete(prompt)

    def _extract_json(text: str) -> Optional[dict]:
        t = (text or "").strip()
        if not t:
            return None

        # 1) Попробуем извлечь из markdown-блока ```json ... ```
        if "```" in t:
            import re

            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass

        # 2) Попробуем по границам JSON-объекта
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = t[start : end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                return None
        return None

    def _normalize_task_fields(task: dict) -> dict:
        # Тонкая нормализация под нашу модель, чтобы не падать в fallback из-за “agent|user” и т.п.
        owner = task.get("owner")
        if isinstance(owner, str):
            ov = owner.strip()
            if ov in {"agent|user", "user|agent", "agent, user", "user, agent"}:
                ov = "agent"
            if ov not in {"agent", "user"}:
                ov = "agent"
            task["owner"] = ov
        else:
            task["owner"] = "agent"

        pr = task.get("priority")
        if isinstance(pr, str):
            pv = pr.strip().lower()
            if pv in {"low|medium|high", "medium|low|high"}:
                pv = "medium"
            if pv not in {"low", "medium", "high"}:
                pv = "medium"
            task["priority"] = pv
        else:
            task["priority"] = "medium"

        due = task.get("due_at")
        if isinstance(due, str):
            d = due.strip()
            # Если модель вернула плейсхолдер, убираем дедлайн, чтобы не падать в fallback.
            if "YYYY-MM-DD" in d and "THH:MM:SS" in d:
                task["due_at"] = None
            elif "YYYY-MM-DD" in d:
                task["due_at"] = None
        return task

    # Пытаемся распарсить JSON, иначе — fallback.
    try:
        data = _extract_json(resp.text)
        if data is None:
            raise ValueError("No JSON found")

        if isinstance(data.get("checklist"), list):
            normalized_tasks: list[dict] = []
            for item in data["checklist"]:
                if isinstance(item, dict):
                    normalized_tasks.append(_normalize_task_fields(item))
            data["checklist"] = normalized_tasks

        try:
            plan = PlanDraft.model_validate(data)
        except Exception:  # noqa: BLE001
            # Вторая попытка: дедлайны иногда приходят в “не тем” формате — обнуляем и валидируем снова.
            if isinstance(data.get("checklist"), list):
                for item in data["checklist"]:
                    if isinstance(item, dict):
                        item["due_at"] = None
            plan = PlanDraft.model_validate(data)
    except Exception:  # noqa: BLE001
        plan = _fallback_plan(profile)
        plan.concept_summary = plan.concept_summary + "\n\n" + "Примечание: LLM-ответ не удалось распарсить как JSON."

    # Нормализуем due_at (если LLM отдал строки)
    normalized: list[TaskItem] = []
    for t in plan.checklist:
        due = t.due_at
        if isinstance(due, str):
            try:
                due = datetime.fromisoformat(due)
            except Exception:  # noqa: BLE001
                due = None
        normalized.append(
            TaskItem(
                id=t.id,
                title=t.title,
                description=t.description,
                due_at=due,
                status=t.status,
                owner=t.owner,
                priority=t.priority,
            )
        )
    plan.checklist = normalized
    return plan


def plan_llm_source(plan: PlanDraft) -> str:
    marker = "Примечание: LLM-ответ не удалось распарсить как JSON."
    return "fallback" if marker in (plan.concept_summary or "") else "gigachat"

