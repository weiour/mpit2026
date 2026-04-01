from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from birthday_agent.llm.base import LLMClient
from birthday_agent.memory.db import AgentDB
from birthday_agent.models import PlanDraft, TaskItem, UserProfile
from birthday_agent.planners.core import generate_plan
from birthday_agent.scheduler import ReminderScheduler


def _norm_list(s: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[,;]\s*|\n+", s) if p.strip()]
    return parts


@dataclass
class BirthdayAgent:
    console: Console
    db: AgentDB
    llm: LLMClient
    scheduler: ReminderScheduler
    autonomy_level: int = 1
    user_id: str = "local_user"

    def run_cli(self) -> None:
        self.console.print(Panel.fit("Автономный агент: организация дня рождения", style="bold"))

        profile = self.db.load_profile(self.user_id)
        self._collect_profile(profile)
        self.db.save_profile(profile)

        self.console.print("\n[bold]Генерирую концепцию и план...[/bold]")
        plan = generate_plan(profile, self.llm)
        self.db.save_plan(self.user_id, plan)

        self._render_plan(plan)
        self._schedule_reminders(plan)

        self.console.print(
            "\nГотово. План сохранён. Можно перезапустить, чтобы продолжить с сохранёнными данными."
        )

    def _ask(self, prompt: str, default: Optional[str] = None) -> str:
        suffix = f" (Enter = {default})" if default else ""
        return self.console.input(f"[bold]{prompt}[/bold]{suffix}\n> ").strip() or (default or "")

    def _collect_profile(self, profile: UserProfile) -> None:
        self.console.print("\nСоберу предпочтения (можно коротко; пропускайте Enter).")

        name = self._ask("Как к вам обращаться?", profile.name or "")
        profile.name = name or profile.name

        city = self._ask("Город/район (для локаций и доставки)?", profile.city or "")
        profile.city = city or profile.city

        bday = self._ask("Дата праздника (YYYY-MM-DD), если известна", "")
        if bday:
            try:
                profile.birthday_date = datetime.strptime(bday, "%Y-%m-%d").date()
            except ValueError:
                self.console.print("Не распознал дату — пропускаю.")

        budget = self._ask("Бюджет (руб), примерно", str(profile.budget_rub or ""))
        if budget:
            try:
                profile.budget_rub = int(budget)
            except ValueError:
                self.console.print("Не распознал бюджет — пропускаю.")

        guests = self._ask("Сколько гостей ожидаете?", str(profile.guests_count or ""))
        if guests:
            try:
                profile.guests_count = int(guests)
            except ValueError:
                self.console.print("Не распознал число — пропускаю.")

        fmt = self._ask("Формат (home/restaurant/outdoor/mixed)", profile.format or "")
        if fmt in {"home", "restaurant", "outdoor", "mixed"}:
            profile.format = fmt  # type: ignore[assignment]

        vibe = self._ask("Ключевые слова атмосферы (например: уютно, шумно, без алкоголя)", "")
        if vibe:
            profile.vibe_keywords = _norm_list(vibe)

        diet = self._ask("Ограничения в еде (веган, без глютена, аллергии) — через запятую", "")
        if diet:
            profile.dietary_restrictions = _norm_list(diet)

        dislikes = self._ask("Что точно НЕ хотите (шумные клубы, караоке, сюрпризы и т.д.)", "")
        if dislikes:
            profile.dislikes = _norm_list(dislikes)

        must = self._ask("Что обязательно должно быть (торт, фотозона, квиз, дети и т.д.)", "")
        if must:
            profile.must_haves = _norm_list(must)

        contacts = self._ask("Где у вас контакты гостей (заметка: 'в Telegram', 'в телефоне'...)", "")
        profile.contacts_note = contacts or profile.contacts_note

    def _render_plan(self, plan: PlanDraft) -> None:
        self.console.print("\n" + str(Panel.fit(plan.concept_title, subtitle="Концепция", style="bold green")))
        self.console.print(plan.concept_summary)

        def _list_panel(title: str, items: list[str]) -> None:
            content = "\n".join([f"- {x}" for x in items]) if items else "—"
            self.console.print(Panel(content, title=title))

        _list_panel("Локации", plan.venue_ideas)
        _list_panel("Меню", plan.menu_ideas)
        _list_panel("Развлечения", plan.entertainment_ideas)
        _list_panel("Оформление", plan.decor_ideas)
        _list_panel("Подарки", plan.gift_ideas)

        self.console.print(Panel(plan.invitation_text, title="Текст приглашения"))

        table = Table(title="Чек-лист подготовки")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Задача")
        table.add_column("Дедлайн")
        table.add_column("Кто")
        table.add_column("Приоритет")

        for t in plan.checklist:
            due = t.due_at.isoformat(sep=" ", timespec="minutes") if t.due_at else "—"
            table.add_row(t.id, t.title, due, t.owner, t.priority)
        self.console.print(table)

    def _schedule_reminders(self, plan: PlanDraft) -> None:
        # В CLI-режиме напоминания будут печататься в консоль,
        # но только пока процесс жив. Это каркас для будущих интеграций.
        now = datetime.now()

        def printer(msg: str) -> None:
            self.console.print(Panel(msg, title="Напоминание", style="yellow"))

        scheduled = 0
        for t in plan.checklist:
            if not t.due_at:
                continue
            run_at = t.due_at - timedelta(hours=6)
            if run_at <= now:
                continue
            job_id = f"reminder:{self.user_id}:{t.id}"
            self.scheduler.schedule_console_reminder(
                run_at=run_at,
                job_id=job_id,
                message=f"Скоро дедлайн: {t.title} (до {t.due_at})",
                printer=printer,
            )
            scheduled += 1

        if scheduled:
            self.console.print(f"\nЗапланировано напоминаний: {scheduled} (пока приложение запущено).")
        else:
            self.console.print("\nНапоминания не запланированы (нет будущих дедлайнов).")

