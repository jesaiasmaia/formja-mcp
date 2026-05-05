import httpx
import logging
from .config import FORMJA_BASE_URL, FORMJA_API_KEY

logger = logging.getLogger("formja-mcp")


class FormJAError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FormJAClient:
    def __init__(self):
        if not FORMJA_API_KEY:
            raise FormJAError("FORMJA_API_KEY is not configured")
        self.base_url = FORMJA_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {FORMJA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        url = f"{self.base_url}{path}"
        logger.debug(f"{method} {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method, url, headers=self.headers, params=params, json=data
                )
            except httpx.TimeoutException:
                raise FormJAError("Request timed out after 30s")
            except httpx.ConnectError:
                raise FormJAError(f"Cannot connect to {self.base_url}")

            if response.status_code == 401:
                raise FormJAError(
                    "API Key inválida ou expirada. Gere um novo token no painel Developer > Tokens.",
                    401,
                )
            if response.status_code == 403:
                raise FormJAError("Sem permissão para realizar esta ação.", 403)
            if response.status_code == 404:
                raise FormJAError(
                    "Recurso não encontrado. Verifique se o ID está correto.", 404
                )

            if response.status_code >= 400:
                try:
                    body = response.json()
                    msg = (
                        body.get("error")
                        or body.get("message")
                        or body.get("details")
                        or f"Erro HTTP {response.status_code}"
                    )
                    if isinstance(msg, list):
                        msg = "; ".join(
                            str(m.get("message", m)) if isinstance(m, dict) else str(m)
                            for m in msg
                        )
                    raise FormJAError(str(msg), response.status_code)
                except (ValueError, AttributeError):
                    raise FormJAError(
                        f"Erro HTTP {response.status_code}", response.status_code
                    )

            return response.json()

    async def get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict) -> dict:
        return await self._request("POST", path, data=data)

    async def put(self, path: str, data: dict) -> dict:
        return await self._request("PUT", path, data=data)

    async def delete(self, path: str) -> dict:
        return await self._request("DELETE", path)


def extract_list(result: dict, key: str) -> tuple[list, dict]:
    """Extract a list and pagination info from FormJA API response.

    FormJA returns: { success: true, data: { key: [...], total, page, ... } }
    """
    data = result.get("data", {})
    if isinstance(data, list):
        return data, {}
    items = data.get(key, []) if isinstance(data, dict) else []
    meta = {k: v for k, v in data.items() if k != key}
    return items, meta


def extract_item(result: dict, key: str | None = None) -> dict:
    """Extract a single item from FormJA API response.

    FormJA returns: { success: true, data: { key: {...} } } or { success: true, data: {...} }
    """
    data = result.get("data", {})
    if key and isinstance(data, dict) and key in data:
        return data[key]
    return data if isinstance(data, dict) else {}
