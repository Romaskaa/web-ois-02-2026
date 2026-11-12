"""Хранилище в памяти.

Данные живут, пока работает процесс: перезапуск сервера возвращает всё к начальному
состоянию. Это временная замена базы данных.
"""
from datetime import datetime, timedelta, timezone
from itertools import count

TOMSK = timezone(timedelta(hours=7))

CLUBS = {
    1: {"id": 1, "name": "IT-клуб"},
    2: {"id": 2, "name": "Шахматный клуб"},
    3: {"id": 3, "name": "Киноклуб"},
}

ROOMS = {
    1: {"id": 1, "name": "Ауд. 214", "building": "Главный корпус", "capacity": 40},
    2: {"id": 2, "name": "Ауд. 101", "building": "Главный корпус", "capacity": 120},
    3: {"id": 3, "name": "Коворкинг", "building": "Научная библиотека", "capacity": 25},
}

EVENTS = {
    1: {
        "id": 1,
        "title": "Как устроен поиск Яндекса",
        "description": "Лекция выпускника о поисковых системах",
        "club_id": 1,
        "room_id": 1,
        "starts_at": datetime(2026, 11, 20, 18, 0, tzinfo=TOMSK),
        "ends_at": datetime(2026, 11, 20, 20, 0, tzinfo=TOMSK),
        "capacity": 40,
    },
    2: {
        "id": 2,
        "title": "Турнир по шахматам",
        "description": "Блиц, контроль 5+3",
        "club_id": 2,
        "room_id": 2,
        "starts_at": datetime(2026, 11, 22, 12, 0, tzinfo=TOMSK),
        "ends_at": datetime(2026, 11, 22, 16, 0, tzinfo=TOMSK),
        "capacity": 64,
    },
}

_event_ids = count(start=len(EVENTS) + 1)


def next_event_id() -> int:
    return next(_event_ids)


_clubs_ids = count(start=max(CLUBS, default=0) + 1)


def next_club_id() -> int:
    return next(_clubs_ids)