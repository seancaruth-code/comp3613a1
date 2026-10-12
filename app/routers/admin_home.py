from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.listing import ListingRepository
from app.repositories.user import UserRepository
from app.repositories.viewing_request import ViewingRequestRepository
from app.services.viewing_request_service import ViewingRequestService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin", response_class=HTMLResponse, name="admin_home_view")
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    listing_repo = ListingRepository(db)
    request_repo = ViewingRequestRepository(db)
    user_repo = UserRepository(db)
    view_service = ViewingRequestService(request_repo, listing_repo)

    request_rows = []
    for req in view_service.list_for_landlord(user.id):
        listing = listing_repo.get_by_id(req.listing_id)
        student = user_repo.get_by_id(req.student_id)
        request_rows.append({
            "request": req,
            "listing": listing,
            "student": student,
            "messages": view_service.list_messages(req.id),
        })

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "requests": request_rows,
        },
    )


@router.post("/admin/requests/{request_id}/decision", response_class=HTMLResponse, name="respond_to_request")
async def respond_to_request(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    request_id: int,
    decision: str = Form(...),
    message: str = Form(""),
):
    service = ViewingRequestService(ViewingRequestRepository(db), ListingRepository(db))
    try:
        service.update_status(request_id, decision, user.id, message)
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    flash(request, f"Viewing request {decision}.", "success")
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=status.HTTP_303_SEE_OTHER)
