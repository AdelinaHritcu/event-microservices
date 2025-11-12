from fastapi import FastAPI
from app.controllers import events, packages, tickets

app = FastAPI(title="Event Manager API")

app.include_router(events.router)
app.include_router(packages.router)
app.include_router(tickets.router)

@app.get("/")
def root():
    return {"_links":{
        "self":{"href":"/"},
        "events":{"href":"/api/event-manager/events"},
        "packages":{"href":"/api/event-manager/packages"},
        "tickets":{"href":"/api/event-manager/tickets"},
    }}
