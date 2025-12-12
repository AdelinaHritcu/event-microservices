import os
from typing import Optional

import httpx

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://api:8000")


class DataServiceClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or DATA_SERVICE_URL

    def create_ticket(self, code: str, event_id: Optional[int], package_id: Optional[int]) -> httpx.Response:
        url = f"{self.base_url}/api/event-manager/tickets/{code}"
        payload = {"event_id": event_id, "package_id": package_id}
        with httpx.Client(timeout=5.0) as client:
            response = client.put(url, json=payload)
        return response

    def get_ticket(self, code: str) -> tuple[Optional[dict], int]:
        url = f"{self.base_url}/api/event-manager/tickets/{code}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
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


data_client = DataServiceClient()
