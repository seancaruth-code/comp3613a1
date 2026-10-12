from typing import Optional

from sqlmodel import SQLModel


class ListingFilter(SQLModel):
    search: Optional[str] = None
    property_type: Optional[str] = None
    max_rent: Optional[float] = None
