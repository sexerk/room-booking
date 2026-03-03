from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_db
from app.schemas.room import Room, RoomCreate, RoomUpdate, RoomAvailability
from app.services.room import get_room_service
from app.models.user import User
from app.api.deps import get_current_admin_user

router = APIRouter(
    # prefix="/rooms",
    tags=["rooms"]
)


@router.get("/", response_model=List[Room])
async def get_rooms(
        skip: int = Query(0, ge=0, description="Сколько пропустить"),
        limit: int = Query(100, ge=1, le=100, description="Сколько вернуть"),
        db: AsyncSession = Depends(get_db)
):
    room_service = await get_room_service(db)
    rooms = await room_service.get_rooms(skip=skip, limit=limit)
    return rooms


@router.get("/availability", response_model=List[RoomAvailability])
async def check_availability(
        start_time: str = Query(..., description="Начало в формате ISO 8601"),
        end_time: str = Query(..., description="Конец в формате ISO 8601"),
        capacity_min: Optional[int] = Query(None, ge=1),
        floor: Optional[int] = Query(None, ge=1),
        amenity_ids: Optional[List[int]] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format. Use ISO 8601 format"
        )

    room_service = await get_room_service(db)
    available_rooms = await room_service.get_available_rooms(
        start_time=start,
        end_time=end,
        min_capacity=capacity_min,
        floor=floor,
        amenity_ids=amenity_ids
    )

    return [RoomAvailability(**room.model_dump(), available=True) for room in available_rooms]


@router.get("/{room_id}", response_model=Room)
async def get_room(
        room_id: int,
        db: AsyncSession = Depends(get_db)
):
    room_service = await get_room_service(db)
    room = await room_service.get_room(room_id)
    return room


@router.post("/", response_model=Room, status_code=status.HTTP_201_CREATED)
async def create_room(
        room_data: RoomCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    room_service = await get_room_service(db)
    room = await room_service.create_room(room_data)
    return room


@router.patch("/{room_id}", response_model=Room)
async def update_room(
        room_id: int,
        room_data: RoomUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    room_service = await get_room_service(db)
    room = await room_service.update_room(room_id, room_data)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
        room_id: int,
        hard_delete: bool = Query(False),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    room_service = await get_room_service(db)
    await room_service.delete_room(room_id, hard_delete=hard_delete)
    return None