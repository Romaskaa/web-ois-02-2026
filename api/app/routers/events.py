from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ValidationError

from app import storage
from app.schemas import ErrorResponse, EventCreate, EventPage, EventRead, EventUpdate

router = APIRouter(prefix="/api/events", tags=["Мероприятия"])

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Мероприятие не найдено"}}
CONFLICT = {409: {"model": ErrorResponse, "description": "Нарушено бизнес-правило (BR-1, BR-6)"}}


def get_event_or_404(event_id: int) -> dict:
    event = storage.EVENTS.get(event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Мероприятие не найдено")
    return event


def check_business_rules(data: dict, event_id: int | None = None) -> None:
    if data["club_id"] not in storage.CLUBS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Клуба {data['club_id']} нет")
    room = storage.ROOMS.get(data["room_id"])
    if room is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Аудитории {data['room_id']} нет")

    # BR-6: мест не больше, чем вмещает аудитория
    if data["capacity"] > room["capacity"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Аудитория «{room['name']}» вмещает {room['capacity']} человек, а указано {data['capacity']}",
        )

    # BR-1: аудитория не занята в это время
    for other in storage.EVENTS.values():
        if other["id"] == event_id or other["room_id"] != data["room_id"]:
            continue
        if data["starts_at"] < other["ends_at"] and other["starts_at"] < data["ends_at"]:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Аудитория «{room['name']}» занята: {other['title']}, "
                f"{other['starts_at']:%d.%m %H:%M}–{other['ends_at']:%H:%M}",
            )


@router.get("", response_model=EventPage, responses={422: {"model": ErrorResponse, "description": "Некорректные параметры поиска"}}, summary="Список мероприятий")
def list_events(
    club_id: Annotated[int | None, Query(description="Только мероприятия этого клуба")] = None,
    date_from: Annotated[date | None, Query(description="Начиная с даты, включительно")] = None,
    date_to: Annotated[date | None, Query(description="По дату, включительно")] = None,
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Мероприятий на странице")] = 20,
    room_id: Annotated[int | None, Query(description="Только мероприятия в указанной аудитории", examples=[1])] = None,
    q: Annotated[str | None, Query(min_length=2, max_length=50, description="Поиск подстроки в названии без учёта регистра, от 2 до 50 символов", examples=["шахмат"])] = None, 
):
    """Мероприятия по возрастанию времени начала. Фильтры можно сочетать."""
    events = sorted(storage.EVENTS.values(), key=lambda e: e["starts_at"])
    if club_id is not None:
        events = [e for e in events if e["club_id"] == club_id]
    if date_from is not None:
        events = [e for e in events if e["starts_at"].date() >= date_from]
    if date_to is not None:
        events = [e for e in events if e["starts_at"].date() <= date_to]
    if room_id is not None:
        events = [e for e in events if e["room_id"] == room_id]
    if q is not None:
        needle = q.casefold()
        events = [e for e in events if needle in e["title"].casefold()]

    start = (page - 1) * size
    return {"items": events[start : start + size], "total": len(events), "page": page, "size": size}


@router.get("/{event_id}", response_model=EventRead, responses=NOT_FOUND, summary="Одно мероприятие")
def get_event(event_id: int):
    return get_event_or_404(event_id)


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    responses=CONFLICT,
    summary="Создать мероприятие",
)
def create_event(payload: EventCreate):
    """Проверяет, что аудитория свободна (BR-1) и вмещает всех участников (BR-6)."""
    data = payload.model_dump()
    check_business_rules(data)
    event = {"id": storage.next_event_id(), **data}
    storage.EVENTS[event["id"]] = event
    return event


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    responses={**NOT_FOUND, **CONFLICT},
    summary="Изменить мероприятие",
)
def update_event(event_id: int, payload: EventUpdate):
    """Меняет только переданные поля. Результат проверяется по тем же правилам, что и при создании."""
    event = get_event_or_404(event_id)
    merged = {**event, **payload.model_dump(exclude_unset=True)}
    try:
        checked = EventCreate.model_validate(merged).model_dump()
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False, include_input=False)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, errors) from exc
    check_business_rules(checked, event_id=event_id)
    event.update(checked)
    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Удалить мероприятие",
)
def delete_event(event_id: int):
    get_event_or_404(event_id)
    del storage.EVENTS[event_id]
