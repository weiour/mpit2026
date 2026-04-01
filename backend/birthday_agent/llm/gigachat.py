from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import requests
import uuid

from birthday_agent.llm.base import LLMClient, LLMResponse


@dataclass(frozen=True)
class GigaChatConfig:
    base_url: str
    access_token: str | None
    timeout_s: float = 30.0
    verify_ssl_certs: bool = True
    ca_bundle_file: str | None = None
    model: str = "GigaChat"

    # OAuth inputs (choose one style)
    client_id: str | None = None
    client_secret: str | None = None
    credentials: str | None = None  # Base64(client_id:client_secret) usually

    # Fallback TTL if response doesn't include expires_in
    access_token_expire_minutes: int = 10080
    token_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    scope: str = "GIGACHAT_API_PERS"


class GigaChatClient(LLMClient):
    def __init__(self, config: GigaChatConfig):
        self._cfg = config
        self._cached_access_token: str | None = config.access_token
        self._token_expires_at: float | None = None  # unix timestamp (seconds)

    @classmethod
    def from_env(cls) -> "GigaChatClient":
        base_url = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
        token = os.getenv("GIGACHAT_ACCESS_TOKEN") or None

        verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "true").strip().lower()
        verify_ssl_certs = not (verify_ssl in {"0", "false", "no", "off"})

        ca_bundle_file = os.getenv("GIGACHAT_CA_BUNDLE_FILE") or None
        model = os.getenv("GIGACHAT_MODEL", "GigaChat")
        credentials = os.getenv("GIGACHAT_CREDENTIALS") or None
        client_id = os.getenv("GIGACHAT_CLIENT_ID") or None
        client_secret = os.getenv("GIGACHAT_CLIENT_SECRET") or None

        ttl_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or os.getenv("GIGACHAT_ACCESS_TOKEN_EXPIRE_MINUTES") or "10080"
        try:
            ttl_min = int(ttl_raw)
        except ValueError:
            ttl_min = 10080

        scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        token_url = os.getenv("GIGACHAT_TOKEN_URL") or "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        return cls(
            GigaChatConfig(
                base_url=base_url.rstrip("/"),
                access_token=token,
                verify_ssl_certs=verify_ssl_certs,
                ca_bundle_file=ca_bundle_file,
                model=model,
                credentials=credentials,
                client_id=client_id,
                client_secret=client_secret,
                access_token_expire_minutes=ttl_min,
                token_url=token_url,
                scope=scope,
            )
        )

    def is_configured(self) -> bool:
        return bool(self._cfg.access_token) or bool(self._cfg.credentials) or (bool(self._cfg.client_id) and bool(self._cfg.client_secret))

    def _now_ts(self) -> float:
        import time

        return time.time()

    def _token_valid(self) -> bool:
        if not self._cached_access_token:
            return False
        if self._token_expires_at is None:
            return True
        return self._now_ts() < self._token_expires_at - 20  # small early refresh window

    def _get_access_token(self) -> str | None:
        """
        Returns access token (cached if still valid).
        Supports:
        - direct token in GIGACHAT_ACCESS_TOKEN
        - OAuth2 client_credentials using either:
          - GIGACHAT_CREDENTIALS (Base64(client_id:client_secret))
          - or GIGACHAT_CLIENT_ID + GIGACHAT_CLIENT_SECRET
        """
        if self._token_valid():
            return self._cached_access_token

        payload = {"scope": self._cfg.scope}

        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            # Required per docs: unique uuid4
            "RqUID": str(uuid.uuid4()),
        }

        # docs: Authorization: Basic authorization_key
        if self._cfg.credentials:
            headers["Authorization"] = f"Basic {self._cfg.credentials}"
        else:
            if not (self._cfg.client_id and self._cfg.client_secret):
                return None
            raw = f"{self._cfg.client_id}:{self._cfg.client_secret}"
            b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {b64}"

        verify: bool | str = self._cfg.verify_ssl_certs
        if self._cfg.ca_bundle_file:
            verify = self._cfg.ca_bundle_file

        try:
            resp = requests.post(
                self._cfg.token_url,
                headers=headers,
                data=payload,
                timeout=self._cfg.timeout_s,
                verify=verify,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:  # noqa: BLE001
            return None

        token = data.get("access_token") or data.get("token")
        if not isinstance(token, str) or not token.strip():
            # Some versions return token inside "result"
            token = data.get("result", {}).get("access_token")

        if not isinstance(token, str) or not token.strip():
            return None

        self._cached_access_token = token.strip()

        # docs may return expires_at in ms timestamp
        expires_at = data.get("expires_at")
        if isinstance(expires_at, (int, float)) and expires_at > 1e10:
            # ms since epoch
            self._token_expires_at = float(expires_at) / 1000.0
        else:
            ttl_min = self._cfg.access_token_expire_minutes
            self._token_expires_at = self._now_ts() + ttl_min * 60
        return self._cached_access_token

    def complete(self, prompt: str) -> LLMResponse:
        access_token = self._get_access_token()
        if not access_token:
            return LLMResponse(
                text=(
                    "GigaChat не настроен (нет токена/credentials). "
                    "Я сгенерировал результат по шаблону.\n\n"
                    + self._fallback(prompt)
                )
            )

        # Минимальный адаптер: ожидается совместимый endpoint /chat/completions.
        # Если у вас другой формат API — адаптируйте этот метод под вашу схему.
        url = f"{self._cfg.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._cfg.model,
            "messages": [
                {"role": "system", "content": "Ты полезный ассистент-организатор дня рождения."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            verify: bool | str = self._cfg.verify_ssl_certs
            if self._cfg.ca_bundle_file:
                verify = self._cfg.ca_bundle_file
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._cfg.timeout_s,
                verify=verify,
            )
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-like: choices[0].message.content
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not isinstance(text, str) or not text.strip():
                text = data.get("choices", [{}])[0].get("text", "")
            if not isinstance(text, str) or not text.strip():
                text = data.get("result") or ""
            if not isinstance(text, str) or not text.strip():
                text = str(data)
            return LLMResponse(text=text.strip())
        except Exception as e:  # noqa: BLE001
            return LLMResponse(
                text=(
                    "Не удалось получить ответ от GigaChat (использую fallback).\n"
                    f"Причина: {type(e).__name__}: {e}\n\n"
                    + self._fallback(prompt)
                )
            )

    def _fallback(self, prompt: str) -> str:
        return (
            "Идеи (шаблон):\n"
            "- Концепт: уютная вечеринка/ужин с активностью (квиз/настолки).\n"
            "- Локация: дом или небольшое кафе рядом.\n"
            "- Меню: 2–3 закуски, салат, горячее, торт, 2 напитка.\n"
            "- Развлечения: плейлист, мини‑квиз про именинника, фотозона.\n"
            "- Подарки: впечатление/сертификат, полезная вещь по хобби, аксессуар.\n\n"
            "Запрос был:\n"
            + prompt[:1200]
        )

