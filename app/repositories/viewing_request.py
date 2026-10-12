from datetime import date, time

from sqlmodel import Session, select

from app.models.listing import Listing
from app.models.viewing_request import RequestMessage, ViewingRequest


class ViewingRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(
        self,
        *,
        listing_id: int,
        student_id: int,
        view_date: date | None,
        view_time: time | None,
        comments: str = "",
    ) -> ViewingRequest:
        request = ViewingRequest(
            listing_id=listing_id,
            student_id=student_id,
            view_date=view_date,
            view_time=view_time,
            comments=comments,
            status="pending",
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_by_id(self, request_id: int) -> ViewingRequest | None:
        return self.db.get(ViewingRequest, request_id)

    def list_for_student(self, student_id: int) -> list[ViewingRequest]:
        return self.db.exec(
            select(ViewingRequest).where(ViewingRequest.student_id == student_id)
        ).all()

    def list_for_landlord(self, landlord_id: int) -> list[ViewingRequest]:
        return self.db.exec(
            select(ViewingRequest)
            .join(Listing, ViewingRequest.listing_id == Listing.id)
            .where(Listing.landlord_id == landlord_id)
            .order_by(ViewingRequest.view_date.asc(), ViewingRequest.view_time.asc())
        ).all()

    def list_messages(self, request_id: int) -> list[RequestMessage]:
        return self.db.exec(
            select(RequestMessage)
            .where(RequestMessage.request_id == request_id)
            .order_by(RequestMessage.id.asc())
        ).all()

    def update_status(
        self,
        request_id: int,
        status: str,
        landlord_id: int | None = None,
        message: str = "",
        sender_id: int | None = None,
    ) -> ViewingRequest:
        request = self.db.get(ViewingRequest, request_id)
        if request is None:
            raise ValueError("Viewing request not found")

        if landlord_id is not None:
            listing = self.db.get(Listing, request.listing_id)
            if listing is None or listing.landlord_id != landlord_id:
                raise ValueError("You do not have access to this viewing request")

        if status not in {"pending", "accepted", "declined", "cancelled"}:
            raise ValueError("Invalid viewing request status")

        request.status = status
        self.db.add(request)
        if message.strip():
            if sender_id is None:
                raise ValueError("A response sender is required")
            self.db.add(
                RequestMessage(
                    request_id=request.id,
                    sender_id=sender_id,
                    content=message.strip(),
                )
            )
        self.db.commit()
        self.db.refresh(request)
        return request
