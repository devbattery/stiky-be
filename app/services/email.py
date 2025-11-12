from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class ResendClient:
    def __init__(self, api_key: str, base_url: str = "https://api.resend.com") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def send_otp_email(self, *, email: str, code: str, expires_in_minutes: int) -> None:
        payload: dict[str, Any] = {
            "from": settings.mail.from_email,
            "to": [email],
            "subject": "[Stiky] 로그인 인증 코드를 보내 드립니다.",
            "text": f"인증 코드: {code}. {expires_in_minutes} 분 남았습니다.",
        }
        if settings.mail.otp_template_id:
            payload["template_id"] = settings.mail.otp_template_id
            payload["data"] = {"code": code, "expires_in": expires_in_minutes}
        else:
            payload["html"] = f"<p>인증 코드: <strong>{code}</strong>.</p>"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/emails", json=payload, headers=headers)
            response.raise_for_status()


resend_client = ResendClient(settings.mail.api_key)
