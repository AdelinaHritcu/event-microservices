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

    def get_event(self, event_id: int, token: Optional[str] = None) -> Optional[dict]:
        url = f"{self.base_url}/api/event-manager/events/{event_id}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=self._headers(token))
        if response.status_code == 200:
            return response.json()
        return None

    def get_package(self, package_id: int, token: Optional[str] = None) -> Optional[dict]:
        url = f"{self.base_url}/api/event-manager/event-packets/{package_id}"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=self._headers(token))
        if response.status_code == 200:
            return response.json()
        return None

    def get_package_events(self, package_id: int, token: Optional[str] = None) -> list[dict]:
        url = f"{self.base_url}/api/event-manager/event-packets/{package_id}/events"
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=self._headers(token))
        if response.status_code == 200:
            return response.json().get("items", [])
        return []

    def list_owner_ticket_codes(
        self, token: str, event_id: Optional[int] = None, package_id: Optional[int] = None
    ) -> list[dict]:
        """
        Tickets for the events/packages owned by the caller (owner-event).
        Event WebService filters by the owner taken from the forwarded token.
        """
        url = f"{self.base_url}/api/event-manager/tickets"
        params: dict = {"items_per_page": 100}
        if event_id is not None:
            params["event_id"] = event_id
        if package_id is not None:
            params["package_id"] = package_id

        out: list[dict] = []
        page = 1
        with httpx.Client(timeout=5.0) as client:
            while True:
                r = client.get(url, params={**params, "page": page}, headers=self._headers(token))
                r.raise_for_status()
                body = r.json()
                out.extend(body.get("items", []))
                if page * params["items_per_page"] >= body.get("total_items", 0):
                    return out
                page += 1


data_client = DataServiceClient()
