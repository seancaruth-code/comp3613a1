from app.repositories.listing import ListingRepository


class ListingService:
    def __init__(self, listing_repo: ListingRepository):
        self.listing_repo = listing_repo

    def list_listings(self, *, search: str | None = None, property_type: str | None = None, max_rent: float | None = None):
        return self.listing_repo.list_listings(
            search=search,
            property_type=property_type,
            max_rent=max_rent,
        )

    def saved_ids_for_user(self, user_id: int) -> set[int]:
        return self.listing_repo.saved_ids_for_user(user_id)

    def list_saved_listings(self, user_id: int):
        return self.listing_repo.list_saved_listings(user_id)

    def toggle_save(self, user_id: int, listing_id: int, action: str | None = None) -> bool:
        action_name = (action or "save").lower()
        if action_name == "unsave":
            return self.listing_repo.unsave_listing(user_id, listing_id)
        return self.listing_repo.save_listing(user_id, listing_id)
