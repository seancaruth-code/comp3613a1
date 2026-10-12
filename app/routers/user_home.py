from datetime import datetime
from urllib.parse import urlparse

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.listing import ListingRepository
from app.repositories.viewing_request import ViewingRequestRepository
from app.services.listing_service import ListingService
from app.services.viewing_request_service import ViewingRequestService
from app.utilities.flash import flash
from . import router, templates


def _return_url(request: Request, fallback: str, candidate: str | None = None) -> str:
    for raw_url in (candidate, request.headers.get("referer")):
        if raw_url:
            parsed_url = urlparse(raw_url)
            if not parsed_url.netloc and parsed_url.path.startswith("/") and not raw_url.startswith("//"):
                return parsed_url.path + (f"?{parsed_url.query}" if parsed_url.query else "")
    return fallback


@router.get("/app", response_class=HTMLResponse, name="user_home_view")
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    search: str | None = None,
    property_type: str | None = None,
    max_rent: str | None = None,
    saved_only: bool = False,
):
    service = ListingService(ListingRepository(db))
    saved_ids = service.saved_ids_for_user(user.id)
    max_rent_value: float | None = None
    if max_rent and max_rent.strip():
        try:
            max_rent_value = float(max_rent)
        except ValueError:
            flash(request, "Max rent must be a valid number.", "warning")

    listings = (
        service.list_saved_listings(user.id)
        if saved_only
        else service.list_listings(
            search=search,
            property_type=property_type,
            max_rent=max_rent_value,
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "listings": listings,
            "saved_ids": saved_ids,
            "saved_count": len(saved_ids),
            "search": search or "",
            "property_type": property_type or "",
            "max_rent": max_rent_value,
            "saved_only": saved_only,
        },
    )


@router.get("/app/saved", response_class=HTMLResponse, name="saved_listings_view")
async def saved_listings_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    return await user_home_view(
        request=request,
        user=user,
        db=db,
        saved_only=True,
    )


@router.get("/app/listings/{listing_id}", response_class=HTMLResponse, name="listing_detail_view")
async def listing_detail_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    listing_id: int,
):
    repo = ListingRepository(db)
    listing = repo.get_by_id(listing_id)
    if listing is None:
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    service = ListingService(repo)
    saved_ids = service.saved_ids_for_user(user.id)

    return templates.TemplateResponse(
        request=request,
        name="listing_detail.html",
        context={
            "user": user,
            "listing": listing,
            "saved": listing_id in saved_ids,
        },
    )


@router.post("/app/listings/{listing_id}/request", response_class=HTMLResponse, name="request_viewing")
async def request_viewing(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    listing_id: int,
    view_date: str = Form(...),
    view_time: str = Form(...),
    comments: str = Form(""),
):
    if user.role == "admin":
        flash(request, "Landlords cannot submit student viewing requests.", "warning")
        return RedirectResponse(
            url=request.url_for("listing_detail_view", listing_id=listing_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        parsed_date = datetime.strptime(view_date, "%Y-%m-%d").date()
        parsed_time = datetime.strptime(view_time, "%H:%M").time()
    except ValueError:
        flash(request, "Please choose a valid viewing date and time.", "danger")
        return RedirectResponse(
            url=request.url_for("listing_detail_view", listing_id=listing_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    repo = ListingRepository(db)
    request_service = ViewingRequestService(
        ViewingRequestRepository(db),
        repo,
    )
    request_service.create_request(
        listing_id=listing_id,
        student_id=user.id,
        view_date=parsed_date,
        view_time=parsed_time,
        comments=comments,
    )
    flash(request, "Viewing request submitted. The landlord will review it shortly.", "success")
    return RedirectResponse(
        url=request.url_for("listing_detail_view", listing_id=listing_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/app/save/{listing_id}", response_class=HTMLResponse, name="toggle_saved_listing")
async def toggle_saved_listing(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    listing_id: int,
    action: str = Form(...),
    return_to: str | None = Form(None),
):
    service = ListingService(ListingRepository(db))
    saved = service.toggle_save(user.id, listing_id, action)

    if saved and action.lower() == "save":
        flash(request, "Listing saved to your shortlist.", "success")
    elif not saved and action.lower() == "save":
        flash(request, "This listing is already in your shortlist.", "info")
    else:
        flash(request, "Listing removed from your shortlist.", "info")

    return RedirectResponse(
        url=_return_url(
            request,
            request.url_for("listing_detail_view", listing_id=listing_id),
            return_to,
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )