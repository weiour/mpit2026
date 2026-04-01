from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from birthday_agent.models import PlanDraft, UserProfile


@dataclass
class AgentDB:
    db_path: str

    def __post_init__(self) -> None:
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                  user_id TEXT PRIMARY KEY,
                  profile_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS plan_draft (
                  user_id TEXT PRIMARY KEY,
                  plan_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_message (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  role TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
                  content TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_message_user_id_created_at ON chat_message(user_id, created_at)"
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS auto_result (
                  user_id TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (user_id, kind)
                )
                """
            )
            con.commit()

    def load_profile(self, user_id: str) -> UserProfile:
        with self._connect() as con:
            row = con.execute(
                "SELECT profile_json FROM user_profile WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return UserProfile(user_id=user_id)
            return UserProfile.model_validate_json(row["profile_json"])

    def save_profile(self, profile: UserProfile) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO user_profile (user_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  profile_json=excluded.profile_json,
                  updated_at=excluded.updated_at
                """,
                (profile.user_id, profile.model_dump_json(), now),
            )
            con.commit()

    def load_plan(self, user_id: str) -> Optional[PlanDraft]:
        with self._connect() as con:
            row = con.execute(
                "SELECT plan_json FROM plan_draft WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return PlanDraft.model_validate_json(row["plan_json"])

    def save_plan(self, user_id: str, plan: PlanDraft) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO plan_draft (user_id, plan_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  plan_json=excluded.plan_json,
                  updated_at=excluded.updated_at
                """,
                (user_id, plan.model_dump_json(), now),
            )
            con.commit()

    def export_state(self, user_id: str) -> dict[str, Any]:
        profile = self.load_profile(user_id)
        plan = self.load_plan(user_id)
        return {
            "profile": json.loads(profile.model_dump_json()),
            "plan": (json.loads(plan.model_dump_json()) if plan else None),
            "auto_results": self.load_auto_results(user_id=user_id),
        }

    def add_chat_message(self, *, user_id: str, role: str, content: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as con:
            con.execute(
                "INSERT INTO chat_message (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, content, now),
            )
            con.commit()

    def get_chat_history(self, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT role, content, created_at
                FROM chat_message
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        rows = list(reversed(rows))
        return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]

    def save_auto_result(self, *, user_id: str, kind: str, payload: dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO auto_result (user_id, kind, payload_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, kind) DO UPDATE SET
                  payload_json=excluded.payload_json,
                  updated_at=excluded.updated_at
                """,
                (user_id, kind, json.dumps(payload, ensure_ascii=False), now),
            )
            con.commit()

    def load_auto_results(self, *, user_id: str) -> dict[str, Any]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT kind, payload_json FROM auto_result WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        out: dict[str, Any] = {}
        for r in rows:
            try:
                out[r["kind"]] = json.loads(r["payload_json"])
            except Exception:
                out[r["kind"]] = {"raw": r["payload_json"]}
        return out

