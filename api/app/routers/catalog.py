from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app import storage
from app.schemas import Club, ClubCreate, ErrorResponse, Room

router = APIRouter(prefix="/api", tags=["Справочники"])


@router.get("/clubs", response_model=list[Club], summary="Клубы")
def list_clubs():
    return list(storage.CLUBS.values())


@router.get(
    "/clubs/{club_id}",
    response_model=Club,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Клуб не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Клуб не найден"}
                }
            },
        }
    },
    summary="Один клуб",
)
def get_club(club_id: int):
    club = storage.CLUBS.get(club_id)
    if club is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Клуб не найден")
    return club


@router.get("/rooms", response_model=list[Room], summary="Аудитории")
def list_rooms():
    return list(storage.ROOMS.values())


def club_name_taken(name: str, exclude_id: int | None = None) -> bool:
    normalized = name.casefold()
    return any(
        club_id != exclude_id and club["name"].casefold() == normalized
        for club_id, club in storage.CLUBS.items()
    )


def get_club_or_404(club_id: int) -> dict:
    club = storage.CLUBS.get(club_id)
    if club is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Клуб не найден")
    return club


CLUB_CONFLICT = {
    409: {
        "model": ErrorResponse,
        "description": "Название клуба занято",
        "content": {
            "application/json": {
                "example": {"detail": "Название клуба занято"}
            }
        },
    }
}
CLUB_NOT_FOUND = {
    404: {
        "model": ErrorResponse,
        "description": "Клуб не найден",
        "content": {
            "application/json": {
                "example": {"detail": "Клуб не найден"}
            }
        },
    }
}
VALIDATION_ERROR = {
    422: {
        "model": ErrorResponse,
        "description": "Некорректные входные данные",
        "content": {
            "application/json": {
                "example": {"detail": "body.name: String should have at least 2 characters"}
            }
        },
    }
}
PATH_VALIDATION_ERROR = {
    422: {
        "model": ErrorResponse,
        "description": "Некорректный ID клуба",
        "content": {
            "application/json": {
                "example": {
                    "detail": "path.club_id: Input should be a valid integer"
                }
            }
        },
    }
}


@router.post(
    "/clubs",
    response_model=Club,
    status_code=status.HTTP_201_CREATED,
    responses={**CLUB_CONFLICT, **VALIDATION_ERROR},
    summary="Создать клуб",
    description="Создаёт клуб с уникальным названием без учета регистра.",
)
def create_club(payload: ClubCreate):
    if club_name_taken(payload.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "Название клуба занято")

    club = {"id": storage.next_club_id(), "name": payload.name}
    storage.CLUBS[club["id"]] = club
    return club


@router.patch(
    "/clubs/{club_id}",
    response_model=Club,
    responses={**CLUB_NOT_FOUND, **CLUB_CONFLICT, **VALIDATION_ERROR},
    summary="Переименовать клуб",
    description="Меняет название существующего клуба; название должно быть свободно.",
)
def rename_club(
    club_id: Annotated[int, Path(description="ID переименовываемого клуба", examples=[1])],
    payload: ClubCreate,
):
    club = get_club_or_404(club_id)
    if club_name_taken(payload.name, exclude_id=club_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Название клуба занято")

    club["name"] = payload.name
    return club


@router.delete(
    "/clubs/{club_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **CLUB_NOT_FOUND,
        409: {
            "model": ErrorResponse,
            "description": "У клуба есть мероприятие",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Нельзя удалить клуб: связанных мероприятий - 1"
                    }
                }
            },
        },
        **PATH_VALIDATION_ERROR,
    },
    summary="Удалить клуб",
    description="Удаляет клуб, если с ним не связаны мероприятия.",
)
def delete_club(
    club_id: Annotated[int, Path(description="ID удаляемого клуба", examples=[1])],
):
    get_club_or_404(club_id)
    event_count = sum(
        event["club_id"] == club_id for event in storage.EVENTS.values()
    )
    if event_count:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Нельзя удалить клуб: связанных мероприятий - {event_count}",
        )

    del storage.CLUBS[club_id]
