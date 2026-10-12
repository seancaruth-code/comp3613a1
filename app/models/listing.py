from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class ListingBase(SQLModel):
    title: str = Field(index=True)
    location: str
    property_type: str = Field(index=True)
    rent: float = Field(default=0.0)
    availability: str = Field(default="available")
    bed: int = Field(default=1)
    description: str = ""
    image: str = ""
    landlord_id: int | None = Field(default=None, foreign_key="user.id")


class Listing(ListingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class SavedListing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    listing_id: int = Field(foreign_key="listing.id", index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_saved_listing_user_listing"),
    )
