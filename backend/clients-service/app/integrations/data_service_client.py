import os
from typing import Optional

import httpx

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://api:8000")


class DataServiceClient:
    """
    Chain call Client WebService -> Event WebService.
    The caller's bearer token is forwarded so Event WebService can
    authorize the action on behalf of the current user.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or DATA_SERVICE_URL

    @staticmethod
    def _headers(token: Optional[str]) -> dict:
        return {"Authorization": f"Bearer {token}"} if token else {}

    def create_ticket(
        self, code: str, event_id: Optional[int], package_id: Optional[int], token: Optional[str] = None
    ) -> httpx.Response:
        url = f"{self.base_url}/api/event-manager/tickets/{code}"
        payload = {"event_id": event_id, "package_id": package_id}
        with httpx.Client(timeout=5.0) as client:
            return client.put(url, json=payload, headers=self._headers(token))

    def get_ticket(self, code: str, token: Optional[str] = None) -> tuple[Optional[dict], int]:
        url = f"{self.base_url}/api/event-manager/tickets/{code}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=self._headers(token))
        if response.status_code == 200:
            return response.json(), 200
        return None, response.status_code

    def get_event(self, event_id: int) -> Optional[dict]:
        url = f"{self.base_url}/api/event-manager/events/{event_id}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_package(self, package_id: int) -> Optional[dict]:
        url = f"{self.base_url}/api/event-manager/event-packets/{package_id}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_package_events(self, package_id: int) -> list[dict]:
        url = f"{self.base_url}/api/event-manager/event-packets/{package_id}/events"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
        if response.status_code == 200:
            return response.json().get("items", [])
        return []


data_client = DataServiceClient()
