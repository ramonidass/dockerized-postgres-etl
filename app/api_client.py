from typing import Any, Dict, Optional
import logging
import httpx
from httpx_retry import AsyncRetryClient
import urllib.parse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AsyncAPIClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        auth_header: str = "Authorization",
        auth_prefix: str = "Bearer",
        timeout: float = 30.0,
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        if not base_url:
            raise ValueError("A base URL is required.")
        try:
            urllib.parse.urlparse(base_url)
        except ValueError as e:
            raise ValueError(f"Invalid base_url: {base_url}") from e

        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._auth_header = auth_header
        self._auth_prefix = auth_prefix
        self._default_timeout = timeout
        self._retry_config = retry_config
        self.client: Optional[AsyncRetryClient] = None

    async def __aenter__(self):
        """Asynchronous context manager entry point to create the client."""
        self.client = await self._create_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit point to close the client."""
        if self.client:
            await self.client.aclose()
            logger.info("Asynchronous HTTPX client closed.")

    async def _create_client(self) -> AsyncRetryClient:
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self._api_key:
            default_headers[self._auth_header] = f"{self._auth_prefix} {self._api_key}"

        retry_config = self._retry_config or {
            "max_attempts": 5,
            "backoff_factor": 1,
            "statuses_to_retry": [408, 429, 500, 502, 503, 504],
            "methods_to_retry": ["HEAD", "GET", "POST", "PUT", "DELETE", "PATCH"],
        }

        client = AsyncRetryClient(
            base_url=self.base_url,
            headers=default_headers,
            timeout=self._default_timeout,
            **retry_config,
        )
        logger.info(
            f"Asynchronous API client initialized with base_url: {self.base_url}"
        )
        return client

    async def init(self):
        """Explicitly initialize the client for non-context-manager usage.
        Note: Using the client as an async context manager (async with) is preferred.
        """
        if self.client is None:
            self.client = await self._create_client()

    async def close(self):
        """Explicitly close the client for non-context-manager usage."""
        if self.client:
            await self.client.aclose()
            logger.info("Asynchronous HTTPX client closed.")
            self.client = None

    def _sanitize_params(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Sanitize parameters to avoid logging sensitive data."""
        if not params:
            return {}
        sanitized = params.copy()
        sensitive_keys = {"password", "token", "api_key"}
        for key in sanitized:
            if key.lower() in sensitive_keys:
                sanitized[key] = "****"
        return sanitized

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        if not self.client:
            raise RuntimeError(
                "AsyncAPIClient must be initialized via 'async with' or 'await client.init()'"
            )
        try:
            full_url_for_log = f"{self.client.base_url}/{endpoint.lstrip('/')}"
            logger.info(
                f"Making {method} request to {full_url_for_log} with params={self._sanitize_params(params)}"
            )

            # Merge custom headers with default headers
            request_headers = self.client.headers.copy()
            if headers:
                request_headers.update(headers)

            response = await self.client.request(
                method,
                endpoint,
                params=params,
                json=json_data,
                timeout=timeout or self._default_timeout,
                headers=request_headers,
            )

            response.raise_for_status()

            if response.status_code == 204:
                logger.info(f"Request to {full_url_for_log} returned 204 No Content")
                return None

            # Check if response is JSON
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            logger.warning(f"Non-JSON response received: {content_type}")
            return response.text

        except httpx.HTTPStatusError as http_err:
            error_details = (
                http_err.response.text
                if getattr(http_err, "response", None)
                else "No response text available"
            )
            logger.error(
                f"HTTP error: {http_err} - Status: {http_err.response.status_code if getattr(http_err, 'response', None) else 'N/A'} - Response: {error_details}"
            )
            raise
        except httpx.RequestError as req_err:
            logger.error(f"Request error occurred: {req_err} for {full_url_for_log}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during request to {full_url_for_log}: {e}")
            raise

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._request("POST", endpoint, json_data=data, headers=headers)

    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._request("PUT", endpoint, json_data=data, headers=headers)

    async def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None
    ) -> Any:
        return await self._request("DELETE", endpoint, headers=headers)

    async def patch(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._request("PATCH", endpoint, json_data=data, headers=headers)
