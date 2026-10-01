"""HTTP session helpers for service clients."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session() -> requests.Session:
    """Create a requests session configured with retry behavior for transient failures."""
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
