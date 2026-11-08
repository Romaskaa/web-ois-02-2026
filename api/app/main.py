from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="WEB-ОИС API",
    description="API студенческой афиши мероприятий",
    version="0.1.0"
)

EVENTS = [
    {"id": 1, "title": "Как устроен поиск Яндекса", "club": "IT-клуб", "room": "Аудитория 203"},
    {"id": 2, "title": "Турнир по шахматам", "club": "Шахматный клуб", "room": "Аудитория 311"}
]

CLUBS = [
    {"id": 1, "name": "IT-клуб"},
    {"id": 2, "name": "Шахматный клуб"},
    {"id": 3, "name": "Клуб настольных игр"},
]

ROOMS = [
    {"id": 1, "name": "Аудитория 203", "building": "Главный корпус", "capacity": 30},
    {"id": 2, "name": "Аудитория 311", "building": "Главный корпус", "capacity": 24},
    {"id": 3, "name": "Аудитория 105", "building": "Корпус 2", "capacity": 40},
]


@app.get("/api/health")
def health():
    return { "status": "ok" }


@app.get("/api/events")
def list_events():
    return EVENTS


@app.get("/api/events/{event_id}")
def get_event(event_id: int):
    for event in EVENTS:
        if event["id"] == event_id:
            return event
    raise HTTPException(status_code=404, detail="Мероприятие не найдено")


@app.get("/api/clubs")
def list_clubs():
    return CLUBS


@app.get("/api/clubs/{club_id}")
def get_club(club_id: int):
    for club in CLUBS:
        if club["id"] == club_id:
            return club
    raise HTTPException(status_code=404, detail="Клуб не найден")


@app.get("/api/rooms")
def list_rooms():
    return ROOMS
