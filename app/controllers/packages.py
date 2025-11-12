from fastapi import APIRouter, Depends, HTTPException, Query
from app.controllers.deps import get_db
from app.dtos.schemas import PackageIn
from app.services import packages_service

router = APIRouter(prefix="/api/event-manager/packages", tags=["packages"])

@router.get("")
def list_packages(page:int=Query(0, ge=0), items_per_page:int=Query(10, ge=1, le=100),
                  name:str|None=None, location:str|None=None, db=Depends(get_db)):
    return packages_service.list_packages(page=page, per_page=items_per_page, name=name, location=location)

@router.get("/{pkg_id}")
def get_package(pkg_id:int, db=Depends(get_db)):
    res = packages_service.get_package(pkg_id)
    if not res: raise HTTPException(404, "Package not found")
    return res

@router.post("", status_code=201)
def create_package(data:PackageIn, db=Depends(get_db)):
    return packages_service.create_package(data)

@router.put("/{pkg_id}")
def update_package(pkg_id:int, data:PackageIn, db=Depends(get_db)):
    code, res = packages_service.update_package(pkg_id, data)
    if code == 404: raise HTTPException(404, "Package not found")
    return res

@router.delete("/{pkg_id}", status_code=204)
def delete_package(pkg_id:int, db=Depends(get_db)):
    code = packages_service.delete_package(pkg_id)
    if code == 404: raise HTTPException(404, "Package not found")

@router.post("/{pkg_id}/events/{event_id}", status_code=204)
def add_event(pkg_id:int, event_id:int, allocated_seats:int|None=None, db=Depends(get_db)):
    code = packages_service.add_event(pkg_id, event_id, allocated_seats)
    if code == 404: raise HTTPException(404, "Package or Event not found")

@router.get("/{pkg_id}/events")
def list_events(pkg_id:int, db=Depends(get_db)):
    return packages_service.list_events(pkg_id)
