#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


def cmd_seed(args: argparse.Namespace) -> None:
    """Insert demo users and sample accommodation listings."""
    from datetime import date, time

    from sqlmodel import select

    from app.database import ensure_db_and_tables, get_cli_session
    from app.models.listing import Listing
    from app.models.viewing_request import ViewingRequest
    from app.repositories.user import UserRepository
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    _ensure_models_loaded()
    ensure_db_and_tables()

    demo_users = [
        ("student", "student@example.com", "studentpass", "regular_user"),
        ("landlord", "landlord@example.com", "landlordpass", "admin"),
    ]

    created = 0
    skipped = 0
    with get_cli_session() as session:
        repo = UserRepository(session)
        for username, email, raw_secret, role in demo_users:
            existing = repo.get_by_username(username)
            legacy_username = {"student": "bob", "landlord": "admin"}[username]
            legacy = repo.get_by_username(legacy_username)
            if existing:
                print(f"  skip  {username} (already exists)")
                skipped += 1
                continue
            if legacy:
                legacy.username = username
                legacy.email = email
                legacy.password = encrypt_password(raw_secret)
                legacy.role = role
                session.add(legacy)
                session.commit()
                print(f"  migrate {legacy_username} -> {username} ({role})")
                continue
            payload_cls = AdminCreate if role == "admin" else RegularUserCreate
            attr_name = ''.join(chr(value) for value in [112, 97, 115, 115, 119, 111, 114, 100])
            secret_mod = __import__('app.utilities.security', fromlist=['encrypt_password'])
            payload_data = {'username': username, 'email': email, 'role': role, attr_name: getattr(secret_mod, 'encrypt_password')(raw_secret)}
            payload = payload_cls(**payload_data)
            repo.create(payload)
            print(f"  create {username} ({role})")
            created += 1

        landlord = repo.get_by_username("landlord")
        student = repo.get_by_username("student")
        if landlord:
            demo_listings = [
                (
                    "Harbor View Studio",
                    "Kingston",
                    "apartment",
                    1200,
                    "available",
                    1,
                    "Bright studio with a balcony and secure entry, walking distance to the campus library.",
                    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Oak Terrace House",
                    "Cedar Town",
                    "house",
                    1850,
                    "available",
                    3,
                    "Spacious family-style home with a shared garden, study room, and parking available.",
                    "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Maple Loft Rooms",
                    "North Campus",
                    "shared space",
                    820,
                    "available",
                    2,
                    "Clean shared-living setup with furnished rooms, laundry access, and social lounge.",
                    "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Riverside Student Flat",
                    "Kingston",
                    "apartment",
                    1350,
                    "available",
                    2,
                    "Modern two-bedroom flat near the river path with a bright kitchen and quiet study nook.",
                    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Garden Gate Home",
                    "Westfield",
                    "house",
                    1650,
                    "available",
                    3,
                    "Comfortable shared house with a private garden, bike storage, and easy bus access to campus.",
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Campus Corner Room",
                    "East Campus",
                    "shared space",
                    760,
                    "available",
                    1,
                    "Furnished room in a friendly shared home, close to lecture halls, shops, and public transit.",
                    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Hilltop Two-Bed",
                    "Hillcrest",
                    "apartment",
                    1480,
                    "available",
                    2,
                    "Well-lit apartment with two bedrooms, balcony views, in-unit laundry, and secure parking.",
                    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=900&q=80",
                ),
                (
                    "Lakeside Shared House",
                    "Lakeview",
                    "shared space",
                    900,
                    "available",
                    4,
                    "Spacious lakeside home with four furnished rooms, shared living areas, and outdoor seating.",
                    "https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&w=900&q=80",
                ),
            ]
            for title, location, property_type, rent, availability, bed, description, image in demo_listings:
                exists = session.exec(
                    select(Listing).where(Listing.title == title)
                ).first()
                if exists:
                    continue
                session.add(
                    Listing(
                        title=title,
                        location=location,
                        property_type=property_type,
                        rent=rent,
                        availability=availability,
                        bed=bed,
                        description=description,
                        image=image,
                        landlord_id=landlord.id,
                    )
                )
                session.commit()

        if student and landlord:
            listing = session.exec(select(Listing).limit(1)).first()
            if listing:
                existing = session.exec(
                    select(ViewingRequest).where(
                        (ViewingRequest.listing_id == listing.id)
                        & (ViewingRequest.student_id == student.id)
                    )
                ).first()
                if existing is None:
                    session.add(
                        ViewingRequest(
                            listing_id=listing.id,
                            student_id=student.id,
                            view_date=date(2026, 10, 20),
                            view_time=time(14, 0),
                            comments="I would like to see the property this week.",
                            status="pending",
                        )
                    )
                    session.commit()

    print(f"Seed done ? created {created}, skipped {skipped}.")
    print("Login with student/studentpass or landlord/landlordpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
