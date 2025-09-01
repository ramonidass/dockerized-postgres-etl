
import logging
from typing import Any, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIClient:

    def __init__(self, base_url: str, api_key: Optional[str] = None):

        if not base_url:
            raise ValueError("A base URL is required.")

        self.base_url = base_url
        self.session = self._create_session(api_key)

    def _create_session(self, api_key: Optional[str]) -> requests.Session:

        session = requests.Session()

        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        if api_key:
            session.headers.update(
                {"Authorization": f"api_key: {api_key}"})

        # Retry on 5xx errors, backoff factor applies delays between retries
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={"HEAD", "GET", "POST", "PUT", "DELETE"}
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Any:

        url = self.base_url.rstrip('/') + '/' + endpoint.lstrip('/')

        try:
            logger.info(
                f"Making {method} request to {url} with params={params}")
            response = self.session.request(
                method,
                url,
                params=params,
                json=json_data,
                timeout=timeout
            )

            response.raise_for_status()

            # Handle cases where response might be empty (e.g., 204 No Content)
            if response.status_code == 204:
                return None

            return response.json()

        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        return self._request("POST", endpoint, json_data=data)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        return self._request("PUT", endpoint, json_data=data)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)
