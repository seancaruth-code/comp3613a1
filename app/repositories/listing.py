from typing import Iterable

from sqlmodel import Session, or_, select

from app.models.listing import Listing, SavedListing


class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_listings(
        self,
        *,
        search: str | None = None,
        property_type: str | None = None,
        max_rent: float | None = None,
    ) -> list[Listing]:
        query = select(Listing)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Listing.title.ilike(search_term),
                    Listing.location.ilike(search_term),
                    Listing.description.ilike(search_term),
                )
            )
        if property_type:
            query = query.where(Listing.property_type == property_type)
        if max_rent is not None:
            query = query.where(Listing.rent <= max_rent)

        return self.db.exec(query.order_by(Listing.rent.asc())).all()

    def list_saved_listings(self, user_id: int) -> list[Listing]:
        return self.db.exec(
            select(Listing)
            .join(SavedListing, SavedListing.listing_id == Listing.id)
            .where(SavedListing.user_id == user_id)
            .order_by(Listing.rent.asc())
        ).all()

    def get_by_id(self, listing_id: int) -> Listing | None:
        return self.db.get(Listing, listing_id)

    def saved_ids_for_user(self, user_id: int) -> set[int]:
        rows = self.db.exec(
            select(SavedListing.listing_id).where(SavedListing.user_id == user_id)
        ).all()
        return {int(row) for row in rows}

    def save_listing(self, user_id: int, listing_id: int) -> bool:
        existing = self.db.exec(
            select(SavedListing).where(
                (SavedListing.user_id == user_id) & (SavedListing.listing_id == listing_id)
            )
        ).first()
        if existing is not None:
            return False

        record = SavedListing(user_id=user_id, listing_id=listing_id)
        self.db.add(record)
        self.db.commit()
        return True

    def unsave_listing(self, user_id: int, listing_id: int) -> bool:
        row = self.db.exec(
            select(SavedListing).where(
                (SavedListing.user_id == user_id) & (SavedListing.listing_id == listing_id)
            )
        ).first()
        if row is None:
            return False

        self.db.delete(row)
        self.db.commit()
        return True
