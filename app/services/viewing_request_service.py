from datetime import date, time

from app.repositories.listing import ListingRepository
from app.repositories.viewing_request import ViewingRequestRepository


class ViewingRequestService:
    def __init__(self, repository: ViewingRequestRepository, listing_repository: ListingRepository):
        self.repository = repository
        self.listing_repository = listing_repository

    def create_request(
        self,
        *,
        listing_id: int,
        student_id: int,
        view_date: date | None,
        view_time: time | None,
        comments: str = "",
    ):
        listing = self.listing_repository.get_by_id(listing_id)
        if listing is None:
            raise ValueError("Listing not found")

        return self.repository.create_request(
            listing_id=listing_id,
            student_id=student_id,
            view_date=view_date,
            view_time=view_time,
            comments=comments,
        )

    def list_for_student(self, student_id: int):
        return self.repository.list_for_student(student_id)

    def list_for_landlord(self, landlord_id: int):
        return self.repository.list_for_landlord(landlord_id)

    def update_status(self, request_id: int, status: str, landlord_id: int, message: str = ""):
        return self.repository.update_status(
            request_id,
            status,
            landlord_id=landlord_id,
            message=message,
            sender_id=landlord_id,
        )

    def list_messages(self, request_id: int):
        return self.repository.list_messages(request_id)
