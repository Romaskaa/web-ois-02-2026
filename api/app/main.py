from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import catalog, events, system

TAGS = [
    {"name": "Мероприятия", "description": "Афиша: создание, просмотр, изменение и удаление."},
    {"name": "Справочники", "description": "Клубы и аудитории."},
    {"name": "Служебное", "description": "Проверка, что сервис жив."},
]

app = FastAPI(
    title="WEB-ОИС API",
    description="API студенческой афиши мероприятий. Бизнес-правила BR-1…BR-10 — в docs/tz.md.",
    version="0.2.0",
    openapi_tags=TAGS,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    details = "; ".join(
        f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
        for error in exc.errors()
    )
    return JSONResponse(status_code=422, content={"detail": details})


app.include_router(system.router)
app.include_router(catalog.router)
app.include_router(events.router)
