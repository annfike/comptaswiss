"""ComptaSwiss : comptabilité locale en partie double."""

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.accounting import (
    account_groups,
    account_ledger,
    balance_sheet,
    blank_lines,
    decorate_account,
    decorate_analytic,
    default_date_for,
    format_chf,
    income_statement,
    journal_entries,
    lines_from_entry,
    parse_entry_form,
    snapshot,
    swiss_date,
    trial_balance,
    validate_account_fields,
    validate_analytic_fields,
)
from app.db import (
    account_has_lines,
    analytic_has_lines,
    connect,
    current_settings,
    db_path,
    delete_account,
    delete_analytic,
    delete_entry,
    fetch_account,
    fetch_accounts,
    fetch_analytic,
    fetch_analytics,
    fetch_entry,
    init_db,
    insert_account,
    insert_analytic,
    next_piece,
    replace_entry,
    set_setting,
    update_account,
    update_analytic,
    year_choices,
)
from app.i18n import FLASH, STRINGS, bundle, t, tconfirm, tf

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.globals["t"] = t
templates.env.globals["tf"] = tf
templates.env.globals["tconfirm"] = tconfirm
templates.env.globals["L"] = STRINGS
templates.env.globals["FLASH"] = FLASH
templates.env.filters["chf"] = format_chf
templates.env.filters["sdate"] = swiss_date


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


def selected_year(request, form=None):
    raw = None
    if form is not None:
        raw = form.get("year")
    if not raw:
        raw = request.query_params.get("year")
    if raw and str(raw).isdigit():
        year = int(raw)
        if 1990 <= year <= 2100:
            return year
    return date.today().year


def redirect(url):
    return RedirectResponse(url, status_code=303)


def safe_next(raw):
    if not raw or not str(raw).startswith("/") or str(raw).startswith("//"):
        return "/"
    return str(raw)


def render(request, template_name, status_code=200, **extra):
    year = extra.pop("year", None)
    if year is None:
        year = selected_year(request)
    with connect() as conn:
        settings = current_settings(conn)
        years = year_choices(conn, year)
    pairs = [(key, value) for key, value in request.query_params.multi_items() if key != "msg"]
    if not any(key == "year" for key, _value in pairs):
        pairs.append(("year", str(year)))
    query = urlencode(pairs)
    payload = {
        "sec": settings["secondary_lang"],
        "year": year,
        "years": years,
        "company": settings["company_name"],
        "page": "",
        "msg": request.query_params.get("msg", ""),
        "today": date.today().isoformat(),
        "here": request.url.path + (("?" + query) if query else ""),
        "db_file": str(db_path()),
    }
    payload.update(extra)
    html = templates.get_template(template_name).render(**payload)
    return HTMLResponse(html, status_code=status_code)


def entry_choices(conn, sec):
    accounts = [decorate_account(row, sec) for row in fetch_accounts(conn)]
    analytics = [decorate_analytic(row, sec) for row in fetch_analytics(conn)]
    return {"groups": account_groups(accounts, sec), "analytics": analytics}


@app.get("/")
def home(request: Request):
    year = selected_year(request)
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        figures = snapshot(conn, year)
        recent = journal_entries(conn, year, sec, limit=8)
    return render(
        request,
        "dashboard.html",
        page="home",
        year=year,
        figures=figures,
        recent=recent,
    )


@app.get("/journal")
def journal(request: Request):
    year = selected_year(request)
    text = request.query_params.get("q", "")
    compte = request.query_params.get("compte", "")
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        entries = journal_entries(conn, year, sec, text=text, account_code=compte)
    return render(
        request,
        "journal.html",
        page="journal",
        year=year,
        entries=entries,
        q=text,
        compte=compte,
    )


@app.get("/ecritures/nouvelle")
def new_entry(request: Request):
    year = selected_year(request)
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        form = blank_lines(next_piece(conn, year), default_date_for(year))
        choices = entry_choices(conn, sec)
    return render(
        request,
        "entry_form.html",
        page="entry",
        year=year,
        entry_id=None,
        meta=form["meta"],
        lines=form["lines"],
        errors=form["errors"],
        **choices,
    )


@app.post("/ecritures")
async def create_entry(request: Request):
    form = await request.form()
    return await _save_entry(request, form, None)


@app.post("/ecritures/analytique")
async def create_entry_analytic(request: Request):
    form = await request.form()
    raw_id = str(form.get("account_id") or "").strip()
    if not raw_id.isdigit():
        raise HTTPException(404)
    account_id = int(raw_id)
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            raise HTTPException(404)
        sec = current_settings(conn)["secondary_lang"]
        fields, errors = validate_analytic_fields(
            {
                "code": form.get("code"),
                "name_fr": form.get("name_fr"),
                "name_de": form.get("name_de"),
                "name_ru": form.get("name_ru"),
                "active": "1",
            },
            conn,
            account_id,
        )
        if errors:
            return JSONResponse(
                {"ok": False, "messages": [bundle(key, sec) for key in errors]},
                status_code=400,
            )
        new_id = insert_analytic(conn, account_id, fields)
        item = decorate_analytic(fetch_analytic(conn, new_id), sec)
    return {"ok": True, "id": new_id, "account_id": account_id, "label": item["label"]}


@app.get("/ecritures/{entry_id}")
def edit_entry(request: Request, entry_id: int):
    year = selected_year(request)
    with connect() as conn:
        found = fetch_entry(conn, entry_id)
        if found is None:
            missing = True
            payload = {}
        else:
            missing = False
            entry, stored = found
            meta, raw = lines_from_entry(entry, stored)
            sec = current_settings(conn)["secondary_lang"]
            payload = {
                "meta": meta,
                "lines": raw,
                "year": int(entry["entry_date"][:4]),
                **entry_choices(conn, sec),
            }
    if missing:
        raise HTTPException(404)
    return render(
        request,
        "entry_form.html",
        page="journal",
        entry_id=entry_id,
        errors=[],
        **payload,
    )


@app.post("/ecritures/{entry_id}")
async def update_entry(request: Request, entry_id: int):
    form = await request.form()
    return await _save_entry(request, form, entry_id)


async def _save_entry(request, form, entry_id):
    with connect() as conn:
        if entry_id is not None and fetch_entry(conn, entry_id) is None:
            missing = True
        else:
            missing = False
        accounts = {row["id"]: row for row in fetch_accounts(conn)}
        analytics = {row["id"]: row for row in fetch_analytics(conn)}
        meta, clean, errors, raw = parse_entry_form(form, accounts, analytics)
        sec = current_settings(conn)["secondary_lang"]
        choices = entry_choices(conn, sec)
        if not missing and not errors:
            replace_entry(
                conn,
                entry_id,
                meta["entry_date"],
                meta["piece"],
                meta["label"],
                clean,
            )
    if missing:
        raise HTTPException(404)
    if errors:
        year = selected_year(request, form)
        if meta["entry_date"] and str(meta["entry_date"])[:4].isdigit():
            try:
                year = int(str(meta["entry_date"])[:4])
            except ValueError:
                pass
        return render(
            request,
            "entry_form.html",
            page="entry" if entry_id is None else "journal",
            year=year,
            entry_id=entry_id,
            meta=meta,
            lines=raw,
            errors=errors,
            **choices,
        )
    year = int(meta["entry_date"][:4])
    return redirect(f"/journal?year={year}&msg=saved")


@app.post("/ecritures/{entry_id}/supprimer")
async def remove_entry(request: Request, entry_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        found = delete_entry(conn, entry_id)
    if not found:
        raise HTTPException(404)
    return redirect(f"/journal?year={year}&msg=deleted")


@app.get("/plan")
def chart(request: Request):
    show_inactive = request.query_params.get("inactifs") == "1"
    year = selected_year(request)
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        accounts = [decorate_account(row, sec) for row in fetch_accounts(conn)]
        counts = {
            row["account_id"]: row["c"]
            for row in conn.execute(
                "SELECT account_id, COUNT(*) AS c FROM analytics WHERE active = 1 GROUP BY account_id"
            )
        }
    if not show_inactive:
        accounts = [account for account in accounts if account["active"]]
    for account in accounts:
        account["analytic_count"] = counts.get(account["id"], 0)
        account["search"] = " ".join(
            [account["code"], account["name_fr"], account["name_de"], account["name_ru"]]
        ).lower()
    return render(
        request,
        "chart.html",
        page="chart",
        year=year,
        groups=account_groups(accounts, sec),
        show_inactive=show_inactive,
    )


def _account_page(conn, account, sec, fields, errors, analytic_errors, posted_new):
    analytics = [decorate_analytic(row, sec) for row in fetch_analytics(conn, account["id"])]
    return {
        "account": account,
        "fields": fields,
        "analytics": analytics,
        "errors": errors,
        "analytic_errors": analytic_errors,
        "posted_new": posted_new,
        "can_delete": not account_has_lines(conn, account["id"]),
    }


def _empty_analytic():
    return {"code": "", "name_fr": "", "name_de": "", "name_ru": "", "active": 1}


@app.get("/plan/nouveau")
def new_account(request: Request):
    fields = {
        "code": "",
        "name_fr": "",
        "name_de": "",
        "name_ru": "",
        "statement": "asset",
        "analytics_required": 0,
        "is_vat": 0,
        "active": 1,
    }
    return render(
        request,
        "account_form.html",
        page="chart",
        year=selected_year(request),
        account=None,
        fields=fields,
        errors=[],
        analytics=[],
        analytic_errors=[],
        posted_new=_empty_analytic(),
        can_delete=False,
    )


@app.post("/plan")
async def create_account(request: Request):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        fields, errors = validate_account_fields(form, conn)
        new_id = None
        if not errors:
            new_id = insert_account(conn, fields)
    if errors:
        return render(
            request,
            "account_form.html",
            page="chart",
            year=year,
            account=None,
            fields=fields,
            errors=errors,
            analytics=[],
            analytic_errors=[],
            posted_new=_empty_analytic(),
            can_delete=False,
        )
    return redirect(f"/plan/{new_id}?year={year}&msg=account_saved")


@app.get("/plan/{account_id}")
def edit_account(request: Request, account_id: int):
    year = selected_year(request)
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            missing = True
            payload = {}
        else:
            missing = False
            sec = current_settings(conn)["secondary_lang"]
            payload = _account_page(conn, account, sec, account, [], [], _empty_analytic())
    if missing:
        raise HTTPException(404)
    return render(request, "account_form.html", page="chart", year=year, **payload)


@app.post("/plan/{account_id}")
async def save_account(request: Request, account_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            missing = True
            payload = {}
        else:
            missing = False
            fields, errors = validate_account_fields(form, conn, ignore_id=account_id)
            if not errors:
                update_account(conn, account_id, fields)
            sec = current_settings(conn)["secondary_lang"]
            shown = fetch_account(conn, account_id) if not errors else fields
            payload = _account_page(conn, account, sec, shown, errors, [], _empty_analytic())
    if missing:
        raise HTTPException(404)
    if payload["errors"]:
        return render(request, "account_form.html", page="chart", year=year, **payload)
    return redirect(f"/plan/{account_id}?year={year}&msg=account_saved")


@app.post("/plan/{account_id}/supprimer")
async def remove_account(request: Request, account_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            missing = True
            blocked = False
        elif account_has_lines(conn, account_id):
            missing = False
            blocked = True
        else:
            missing = False
            blocked = False
            delete_account(conn, account_id)
    if missing:
        raise HTTPException(404)
    if blocked:
        return redirect(f"/plan/{account_id}?year={year}&msg=err_used")
    return redirect(f"/plan?year={year}&msg=account_deleted")


@app.post("/plan/{account_id}/analytiques")
async def add_analytic(request: Request, account_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            missing = True
            payload = {}
        else:
            missing = False
            fields, errors = validate_analytic_fields(form, conn, account_id)
            if not errors:
                insert_analytic(conn, account_id, fields)
            sec = current_settings(conn)["secondary_lang"]
            posted = _empty_analytic() if not errors else fields
            payload = _account_page(conn, account, sec, account, [], errors, posted)
    if missing:
        raise HTTPException(404)
    if payload["analytic_errors"]:
        return render(request, "account_form.html", page="chart", year=year, **payload)
    return redirect(f"/plan/{account_id}?year={year}&msg=analytic_saved")


@app.post("/analytiques/{analytic_id}")
async def save_analytic(request: Request, analytic_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        analytic = fetch_analytic(conn, analytic_id)
        if analytic is None:
            missing = True
            account_id = None
            errors = []
        else:
            missing = False
            account_id = analytic["account_id"]
            _fields, errors = validate_analytic_fields(
                form, conn, account_id, ignore_id=analytic_id
            )
            if not errors:
                update_analytic(conn, analytic_id, _fields)
    if missing:
        raise HTTPException(404)
    if errors:
        return redirect(f"/plan/{account_id}?year={year}&msg={errors[0]}")
    return redirect(f"/plan/{account_id}?year={year}&msg=analytic_saved")


@app.post("/analytiques/{analytic_id}/supprimer")
async def remove_analytic(request: Request, analytic_id: int):
    form = await request.form()
    year = selected_year(request, form)
    with connect() as conn:
        analytic = fetch_analytic(conn, analytic_id)
        if analytic is None:
            missing = True
            account_id = None
            blocked = False
        else:
            missing = False
            account_id = analytic["account_id"]
            blocked = analytic_has_lines(conn, analytic_id)
            if not blocked:
                delete_analytic(conn, analytic_id)
    if missing:
        raise HTTPException(404)
    if blocked:
        return redirect(f"/plan/{account_id}?year={year}&msg=err_analytic_used")
    return redirect(f"/plan/{account_id}?year={year}&msg=analytic_deleted")


@app.get("/balance")
def trial(request: Request):
    year = selected_year(request)
    detail_values = request.query_params.getlist("detail")
    detail = True if not detail_values else detail_values[-1] != "0"
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        report = trial_balance(conn, year, sec, detail=detail)
    return render(
        request,
        "trial.html",
        page="trial",
        year=year,
        report=report,
        detail=detail,
    )


@app.get("/bilan")
def bilan(request: Request):
    year = selected_year(request)
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        report = balance_sheet(conn, year, sec)
    return render(request, "bilan.html", page="balance", year=year, report=report)


@app.get("/resultat")
def resultat(request: Request):
    year = selected_year(request)
    with connect() as conn:
        sec = current_settings(conn)["secondary_lang"]
        report = income_statement(conn, year, sec)
    return render(request, "resultat.html", page="income", year=year, report=report)


@app.get("/comptes/{account_id}/fiche")
def fiche(request: Request, account_id: int):
    year = selected_year(request)
    raw_filter = request.query_params.get("analytique")
    with connect() as conn:
        account = fetch_account(conn, account_id)
        if account is None:
            missing = True
            payload = {}
        else:
            missing = False
            sec = current_settings(conn)["secondary_lang"]
            analytics = [decorate_analytic(row, sec) for row in fetch_analytics(conn, account_id)]
            known = {row["id"] for row in analytics}
            if raw_filter is None or raw_filter == "":
                analytic_filter = None
            elif raw_filter == "0":
                analytic_filter = 0
            elif raw_filter.isdigit() and int(raw_filter) in known:
                analytic_filter = int(raw_filter)
            else:
                analytic_filter = None
            report = account_ledger(conn, account, year, sec, analytic_filter)
            payload = {
                "account": decorate_account(account, sec),
                "analytics": analytics,
                "analytic_filter": "" if analytic_filter is None else str(analytic_filter),
                "report": report,
            }
    if missing:
        raise HTTPException(404)
    return render(request, "fiche.html", page="ledger", year=year, **payload)


@app.get("/parametres")
def settings(request: Request):
    return render(request, "settings.html", page="settings", year=selected_year(request))


@app.post("/parametres")
async def save_settings(request: Request):
    form = await request.form()
    year = selected_year(request, form)
    name = (form.get("company_name") or "").strip()
    if len(name) > 200:
        name = name[:200]
    lang = form.get("lang") or "ru"
    if lang not in ("ru", "de", "off"):
        lang = "ru"
    with connect() as conn:
        set_setting(conn, "company_name", name)
        set_setting(conn, "secondary_lang", lang)
    return redirect(f"/parametres?year={year}&msg=settings_saved")


@app.post("/parametres/langue")
async def save_language(request: Request):
    form = await request.form()
    lang = form.get("lang") or "ru"
    if lang not in ("ru", "de", "off"):
        lang = "ru"
    with connect() as conn:
        set_setting(conn, "secondary_lang", lang)
    return redirect(safe_next(form.get("next")))


@app.get("/favicon.ico")
def favicon():
    return HTMLResponse(status_code=204)


@app.exception_handler(404)
async def not_found(request: Request, _exc):
    return render(request, "404.html", status_code=404, page="")
