"""
Navigation links towards Client WebService (Lab 3 / 2.2): a potential client is
told where to create/update personal data and where its purchased tickets live.
"""
import os

CLIENTS_PUBLIC_URL = os.getenv("CLIENTS_PUBLIC_URL", "http://localhost:8001").rstrip("/")


def client_links() -> dict:
    base = f"{CLIENTS_PUBLIC_URL}/api/clients"
    return {
        "client-profile": {"href": f"{base}/me", "type": "GET"},
        "client-profile-create": {"href": base, "type": "POST"},
        "client-profile-update": {"href": f"{base}/me", "type": "PUT"},
        "client-tickets": {"href": f"{base}/me/tickets", "type": "GET"},
    }


def buy_ticket_link() -> dict:
    # body: {"event_id": ...} or {"package_id": ...}
    return {"buy-ticket": {"href": f"{CLIENTS_PUBLIC_URL}/api/clients/me/tickets", "type": "POST"}}
