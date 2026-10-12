from datetime import date, time
from typing import Optional

from sqlmodel import Field, SQLModel


class ViewingRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id", index=True)
    student_id: int = Field(foreign_key="user.id", index=True)
    view_date: date | None = None
    view_time: time | None = None
    comments: str = ""
    status: str = Field(default="pending")


class RequestMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="viewingrequest.id", index=True)
    sender_id: int = Field(foreign_key="user.id", index=True)
    content: str
