from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Club(BaseModel):
    id: int
    name: str


class Room(BaseModel):
    id: int
    name: str
    building: str
    capacity: int


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=200, examples=["Как устроен поиск Яндекса"])
    description: str = Field(default="", max_length=5000)
    club_id: int = Field(examples=[1])
    room_id: int = Field(examples=[1])
    starts_at: AwareDatetime = Field(examples=["2026-11-27T18:00:00+07:00"])
    ends_at: AwareDatetime = Field(examples=["2026-11-27T20:00:00+07:00"])
    capacity: int = Field(gt=0, le=1000, examples=[30])


class EventCreate(EventBase):
    @model_validator(mode="after")
    def check_time_order(self):
        # BR-7: окончание позже начала
        if self.ends_at <= self.starts_at:
            raise ValueError("Время окончания должно быть позже времени начала")
        return self


class EventUpdate(BaseModel):
    """Все поля необязательны: меняется только то, что прислали."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    room_id: int | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    capacity: int | None = Field(default=None, gt=0, le=1000)


class EventRead(EventBase):
    id: int


class EventPage(BaseModel):
    items: list[EventRead]
    total: int
    page: int
    size: int


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["Мероприятие не найдено"])


class ClubCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=2,
        max_length=100,
        examples=["Астрономический клуб"],
    )
