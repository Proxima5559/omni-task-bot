import httpx

from app.config import settings
from app.utils.errors import PermanentError, TransientError


class TelegramAPI:
    def __init__(self, token: str | None = None, base_url: str | None = None, timeout: float = 30.0):
        self.token = token or settings.telegram_bot_token
        self.base = (base_url or settings.telegram_api_base_url).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            resp = httpx.request(method, url, timeout=self.timeout, **kwargs)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise TransientError(f"Telegram unreachable: {exc}") from exc
        if resp.status_code == 429 or resp.status_code >= 500:
            raise TransientError(f"Telegram returned {resp.status_code}")
        if resp.status_code >= 400:
            raise PermanentError(f"Telegram returned {resp.status_code}: {resp.text[:200]}")
        return resp

    def _call(self, method: str, payload: dict) -> dict:
        resp = self._request("POST", f"{self.base}/bot{self.token}/{method}", json=payload)
        data = resp.json()
        if not data.get("ok"):
            raise PermanentError(f"Telegram error: {data.get('description')}")
        return data["result"]

    def get_file_path(self, file_id: str) -> str:
        return self._call("getFile", {"file_id": file_id})["file_path"]

    def download_file(self, file_path: str) -> bytes:
        return self._request("GET", f"{self.base}/file/bot{self.token}/{file_path}").content

    def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> None:
        payload: dict = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self._call("editMessageText", payload)