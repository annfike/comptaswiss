"""Écritures et rapports. Tous les montants sont en centimes."""

import re
from dataclasses import dataclass
from datetime import datetime

from app.i18n import STRINGS, bundle, secondary_name

CODE_RE = re.compile(r"[1-9]\d{2,7}")
ANALYTIC_CODE_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]{0,19}")
STATEMENTS = ("asset", "liability", "equity", "pl", "closing")
MAX_CENTS = 10**14

ASSET_GROUPS = (
    (1000, 1099, "g_cash"),
    (1100, 1199, "g_receivables"),
    (1200, 1299, "g_inventory"),
    (1300, 1399, "g_prepaid"),
    (1400, 1499, "g_financial_assets"),
    (1500, 1599, "g_movables"),
    (1600, 1699, "g_property"),
    (1700, 1799, "g_intangible"),
    (1800, 9999, "g_other_assets"),
)
LIABILITY_GROUPS = (
    (2000, 2099, "g_payables"),
    (2100, 2199, "g_st_debt"),
    (2200, 2299, "g_other_st"),
    (2300, 2399, "g_accruals"),
    (2400, 2599, "g_lt_debt"),
    (2600, 2799, "g_provisions"),
    (1, 99999, "g_other_liab"),
)
EQUITY_GROUPS = (
    (2800, 2899, "g_capital"),
    (2900, 2999, "g_reserves"),
    (1, 99999, "g_other_equity"),
)
PL_SEQUENCE = (
    ("g_revenue", 3000, 3999, None),
    ("g_cogs", 4000, 4999, "sub_margin"),
    ("g_staff", 5000, 5999, None),
    ("g_opex", 6000, 6799, None),
    ("g_depr", 6800, 6899, "sub_operating"),
    ("g_financial", 6900, 6999, None),
    ("g_ancillary", 7000, 7999, None),
    ("g_extraordinary", 8000, 8899, None),
    ("g_pl_other", None, None, "sub_before_tax"),
    ("g_tax", 8900, 8999, None),
)


class MoneyError(Exception):
    pass


def parse_money(raw):
    """None si le champ est vide. Entier de centimes sinon."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = re.sub(r"(?i)\b(chf|fr\.?)\b", "", text)
    text = (
        text.replace("'", "")
        .replace("’", "")
        .replace(" ", "")
        .replace("\u00a0", "")
        .replace("\u202f", "")
        .strip()
    )
    if not text:
        return None
    if text[0] == "+":
        text = text[1:]
    if text.startswith("-"):
        raise MoneyError("negative")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        text = text.replace(".", "")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", text):
        raise MoneyError("format")
    if "." in text:
        whole, frac = text.split(".")
        frac = frac.ljust(2, "0")
    else:
        whole, frac = text, "00"
    cents = int(whole) * 100 + int(frac)
    if cents >= MAX_CENTS:
        raise MoneyError("too_big")
    return cents


def format_chf(cents, zeros=False):
    if cents is None or cents == "":
        return ""
    cents = int(cents)
    if cents == 0 and not zeros:
        return ""
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    body = f"{whole:,}".replace(",", "'")
    return f"{sign}{body}.{frac:02d}"


def plain_money(cents):
    whole, frac = divmod(int(cents), 100)
    return f"{whole}.{frac:02d}"


def swiss_date(value):
    if not value:
        return ""
    parts = str(value).split("-")
    if len(parts) != 3:
        return str(value)
    year, month, day = parts
    return f"{day}.{month}.{year}"


def default_date_for(year):
    today = datetime.now().date()
    if today.year == year:
        return today.isoformat()
    return f"{year:04d}-01-01"


def parse_date(raw):
    try:
        parsed = datetime.strptime(str(raw).strip(), "%Y-%m-%d")
    except ValueError:
        return None
    if not 1990 <= parsed.year <= 2100:
        return None
    return parsed.date()


def default_statement(code):
    number = int(code)
    digit = int(code[0])
    if digit == 1:
        return "asset"
    if digit == 2:
        return "equity" if number >= 2800 else "liability"
    if digit == 9:
        return "closing"
    if digit in (3, 4, 5, 6, 7, 8):
        return "pl"
    return "asset"


def split_dc(net_debit_minus_credit):
    if net_debit_minus_credit >= 0:
        return net_debit_minus_credit, 0
    return 0, -net_debit_minus_credit


@dataclass
class Cell:
    before_d: int = 0
    before_c: int = 0
    mov_d: int = 0
    mov_c: int = 0

    def opening_net_dc(self):
        return self.before_d - self.before_c

    def end_net_dc(self):
        return self.opening_net_dc() + self.mov_d - self.mov_c

    def year_d(self):
        return self.mov_d

    def year_c(self):
        return self.mov_c

    def active(self):
        return any((self.before_d, self.before_c, self.mov_d, self.mov_c))


def add_cells(cells):
    total = Cell()
    for cell in cells:
        total.before_d += cell.before_d
        total.before_c += cell.before_c
        total.mov_d += cell.mov_d
        total.mov_c += cell.mov_c
    return total


def load_books(conn, year):
    start = f"{year:04d}-01-01"
    end = f"{year:04d}-12-31"
    rows = conn.execute(
        """
        SELECT l.account_id AS account_id,
               COALESCE(l.analytic_id, 0) AS analytic_id,
               l.side AS side,
               CASE
                 WHEN e.entry_date < ? THEN 'before'
                 WHEN e.entry_date > ? THEN 'after'
                 ELSE 'in'
               END AS placement,
               SUM(l.amount_cents) AS amount
        FROM lines l
        JOIN entries e ON e.id = l.entry_id
        GROUP BY l.account_id,
                 COALESCE(l.analytic_id, 0),
                 l.side,
                 CASE
                   WHEN e.entry_date < ? THEN 'before'
                   WHEN e.entry_date > ? THEN 'after'
                   ELSE 'in'
                 END
        """,
        (start, end, start, end),
    ).fetchall()
    cells = {}
    for row in rows:
        if row["placement"] == "after":
            continue
        key = (row["account_id"], row["analytic_id"])
        cell = cells.get(key)
        if cell is None:
            cell = Cell()
            cells[key] = cell
        bucket = "before" if row["placement"] == "before" else "mov"
        side = "d" if row["side"] == "debit" else "c"
        attr = f"{bucket}_{side}"
        setattr(cell, attr, getattr(cell, attr) + row["amount"])
    accounts = {
        row["id"]: dict(row)
        for row in conn.execute("SELECT * FROM accounts").fetchall()
    }
    analytics = {
        row["id"]: dict(row)
        for row in conn.execute("SELECT * FROM analytics").fetchall()
    }
    return {"cells": cells, "accounts": accounts, "analytics": analytics}


def cells_for_account(books, account_id):
    return [cell for (acc_id, _), cell in books["cells"].items() if acc_id == account_id]


def account_cell(books, account_id):
    return add_cells(cells_for_account(books, account_id))


def trial_figures(cell):
    opening_d, opening_c = split_dc(cell.opening_net_dc())
    closing_d, closing_c = split_dc(cell.end_net_dc())
    return {
        "ouv_d": opening_d,
        "ouv_c": opening_c,
        "mov_d": cell.mov_d,
        "mov_c": cell.mov_c,
        "sol_d": closing_d,
        "sol_c": closing_c,
    }


def _name_bits(row, sec):
    return {"name_fr": row["name_fr"], "sub": secondary_name(row, sec)}


def trial_balance(conn, year, sec, detail=True):
    books = load_books(conn, year)
    rows = []
    totals = {key: 0 for key in ("ouv_d", "ouv_c", "mov_d", "mov_c", "sol_d", "sol_c")}
    account_ids = sorted(
        {account_id for account_id, _ in books["cells"]},
        key=lambda account_id: int(books["accounts"][account_id]["code"]),
    )
    for account_id in account_ids:
        account = books["accounts"][account_id]
        combined = account_cell(books, account_id)
        if not combined.active():
            continue
        figures = trial_figures(combined)
        for key in totals:
            totals[key] += figures[key]
        analytics = []
        if detail:
            parts = []
            for (acc_id, analytic_id), cell in books["cells"].items():
                if acc_id != account_id or not cell.active():
                    continue
                parts.append((analytic_id, cell))
            named = [part for part in parts if part[0] != 0]
            if named:
                parts.sort(key=lambda part: _analytic_sort(books, part[0]))
                for analytic_id, cell in parts:
                    item = trial_figures(cell)
                    if analytic_id == 0:
                        item["sans"] = True
                    else:
                        analytic = books["analytics"][analytic_id]
                        item.update(_name_bits(analytic, sec))
                        item["code"] = analytic["code"]
                        item["sans"] = False
                        item["id"] = analytic_id
                    item["analytic_id"] = analytic_id
                    analytics.append(item)
        row = {
            "id": account_id,
            "code": account["code"],
            "statement": account["statement"],
            "analytics": analytics,
        }
        row.update(_name_bits(account, sec))
        row.update(figures)
        rows.append(row)
    return {"rows": rows, "totals": totals, "balanced": _trial_balanced(totals)}


def _trial_balanced(totals):
    return (
        totals["ouv_d"] == totals["ouv_c"]
        and totals["mov_d"] == totals["mov_c"]
        and totals["sol_d"] == totals["sol_c"]
    )


def _analytic_sort(books, analytic_id):
    if analytic_id == 0:
        return ("~", "")
    analytic = books["analytics"][analytic_id]
    return (analytic["code"].lower(), analytic["name_fr"].lower())


def _group_key(statement, code):
    number = int(code)
    if statement == "asset":
        ranges = ASSET_GROUPS
    elif statement == "liability":
        ranges = LIABILITY_GROUPS
    elif statement == "equity":
        ranges = EQUITY_GROUPS
    else:
        return None
    for low, high, key in ranges:
        if low <= number <= high:
            return key
    if statement == "asset":
        return "g_other_assets"
    if statement == "liability":
        return "g_other_liab"
    return "g_other_equity"


def _position_amount(statement, cell):
    net = cell.end_net_dc()
    if statement == "asset":
        return net
    return -net


def _analytic_rows(books, account_id, sec, amount_of):
    parts = []
    for (acc_id, analytic_id), cell in books["cells"].items():
        if acc_id != account_id:
            continue
        amount = amount_of(cell)
        if amount == 0 and not cell.active():
            continue
        if amount == 0 and cell.year_d() == 0 and cell.year_c() == 0 and statement_year_only(amount_of):
            continue
        if amount == 0:
            continue
        item = {"amount": amount, "analytic_id": analytic_id}
        if analytic_id == 0:
            item["sans"] = True
        else:
            analytic = books["analytics"][analytic_id]
            item["sans"] = False
            item["code"] = analytic["code"]
            item.update(_name_bits(analytic, sec))
        parts.append(item)
    named = [part for part in parts if not part["sans"]]
    if not named:
        return []
    parts.sort(key=lambda part: (part["sans"], part.get("code", "").lower()))
    return parts


def statement_year_only(_amount_of):
    return False


def balance_sheet(conn, year, sec):
    books = load_books(conn, year)
    assets = _statement_side(books, sec, "asset", _position_amount)
    liabilities = _statement_side(books, sec, "liability", _position_amount)
    equity = _statement_side(books, sec, "equity", _position_amount)
    closing_rows = []
    closing_total = 0
    for account in books["accounts"].values():
        if account["statement"] != "closing":
            continue
        cell = account_cell(books, account["id"])
        amount = _position_amount("closing", cell)
        if amount == 0:
            continue
        closing_total += amount
        closing_rows.append(_account_row(books, account, sec, amount, _position_amount))
    closing_rows.sort(key=lambda row: int(row["code"]))
    result_year = 0
    result_prior = 0
    for account in books["accounts"].values():
        if account["statement"] != "pl":
            continue
        cell = account_cell(books, account["id"])
        result_prior += cell.before_c - cell.before_d
        result_year += cell.year_c() - cell.year_d()
    total_assets = sum(row["amount"] for row in assets["accounts"])
    total_passifs = (
        sum(row["amount"] for row in liabilities["accounts"])
        + sum(row["amount"] for row in equity["accounts"])
        + result_year
        + result_prior
        + closing_total
    )
    return {
        "asset_groups": assets["groups"],
        "liability_groups": liabilities["groups"],
        "equity_groups": equity["groups"],
        "closing_rows": closing_rows,
        "result_year": result_year,
        "result_prior": result_prior,
        "total_assets": total_assets,
        "total_passifs": total_passifs,
        "difference": total_assets - total_passifs,
    }


def _account_row(books, account, sec, amount, amount_of):
    row = {
        "id": account["id"],
        "code": account["code"],
        "amount": amount,
        "analytics": _analytic_rows(books, account["id"], sec, amount_of),
    }
    row.update(_name_bits(account, sec))
    return row


def _statement_side(books, sec, statement, amount_of):
    grouped = {key: [] for _, _, key in _ranges_for(statement)}
    accounts = []
    for account in books["accounts"].values():
        if account["statement"] != statement:
            continue
        cell = account_cell(books, account["id"])
        amount = amount_of(statement, cell)
        if amount == 0:
            continue
        row = _account_row(books, account, sec, amount, lambda item, st=statement: amount_of(st, item))
        accounts.append(row)
        grouped.setdefault(_group_key(statement, account["code"]), []).append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: int(row["code"]))
    groups = []
    for _, _, key in _ranges_for(statement):
        rows = grouped.get(key) or []
        if rows:
            groups.append(
                {
                    "key": key,
                    "accounts": rows,
                    "amount": sum(row["amount"] for row in rows),
                }
            )
    return {"groups": groups, "accounts": accounts}


def _ranges_for(statement):
    if statement == "asset":
        return ASSET_GROUPS
    if statement == "liability":
        return LIABILITY_GROUPS
    return EQUITY_GROUPS


def income_statement(conn, year, sec):
    books = load_books(conn, year)
    ranged = {key: [] for key, _, _, _ in PL_SEQUENCE if key != "g_pl_other"}
    other = []
    used = set()
    for account in books["accounts"].values():
        if account["statement"] != "pl":
            continue
        cell = account_cell(books, account["id"])
        if cell.year_d() == 0 and cell.year_c() == 0:
            continue
        number = int(account["code"])
        placed = False
        for key, low, high, _checkpoint in PL_SEQUENCE:
            if low is None:
                continue
            if low <= number <= high:
                ranged[key].append((account, cell))
                used.add(account["id"])
                placed = True
                break
        if not placed:
            other.append((account, cell))
    rows = []
    running = 0
    seen = False

    def emit_accounts(key, pairs):
        nonlocal running, seen
        if not pairs:
            return
        seen = True
        pairs.sort(key=lambda pair: int(pair[0]["code"]))
        rows.append({"type": "section", "key": key})
        section_d = 0
        section_c = 0
        section_amount = 0
        for account, cell in pairs:
            amount = cell.year_c() - cell.year_d()
            section_d += cell.year_d()
            section_c += cell.year_c()
            section_amount += amount
            row = {
                "type": "account",
                "id": account["id"],
                "code": account["code"],
                "debit": cell.year_d(),
                "credit": cell.year_c(),
                "amount": amount,
                "analytics": _income_analytics(books, account["id"], sec),
            }
            row.update(_name_bits(account, sec))
            rows.append(row)
        rows.append(
            {
                "type": "section_total",
                "key": key,
                "debit": section_d,
                "credit": section_c,
                "amount": section_amount,
            }
        )
        running += section_amount

    for key, _low, _high, checkpoint in PL_SEQUENCE:
        if key == "g_pl_other":
            emit_accounts(key, other)
        else:
            emit_accounts(key, ranged.get(key, []))
        if checkpoint and seen:
            rows.append({"type": "subtotal", "key": checkpoint, "amount": running})
    if not seen:
        return {"rows": [], "result": 0}
    rows.append({"type": "total", "key": "result_year", "amount": running})
    return {"rows": rows, "result": running}


def _income_analytics(books, account_id, sec):
    parts = []
    for (acc_id, analytic_id), cell in books["cells"].items():
        if acc_id != account_id:
            continue
        if cell.year_d() == 0 and cell.year_c() == 0:
            continue
        item = {
            "analytic_id": analytic_id,
            "debit": cell.year_d(),
            "credit": cell.year_c(),
            "amount": cell.year_c() - cell.year_d(),
        }
        if analytic_id == 0:
            item["sans"] = True
        else:
            analytic = books["analytics"][analytic_id]
            item["sans"] = False
            item["code"] = analytic["code"]
            item.update(_name_bits(analytic, sec))
        parts.append(item)
    if not any(not part["sans"] for part in parts):
        return []
    parts.sort(key=lambda part: (part["sans"], part.get("code", "").lower()))
    return parts


def snapshot(conn, year):
    sheet = balance_sheet(conn, year, "off")
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM entries WHERE entry_date BETWEEN ? AND ?",
        (f"{year:04d}-01-01", f"{year:04d}-12-31"),
    ).fetchone()["c"]
    return {
        "assets": sheet["total_assets"],
        "result": sheet["result_year"],
        "count": count,
        "balanced": sheet["difference"] == 0,
    }


def journal_entries(conn, year, sec, text="", account_code="", limit=None):
    start = f"{year:04d}-01-01"
    end = f"{year:04d}-12-31"
    clauses = ["e.entry_date BETWEEN ? AND ?"]
    params = [start, end]
    if text.strip():
        clauses.append("(e.label LIKE ? OR e.piece LIKE ?)")
        like = f"%{text.strip()}%"
        params.extend([like, like])
    if account_code.strip():
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM lines l
                JOIN accounts a ON a.id = l.account_id
                WHERE l.entry_id = e.id AND a.code = ?
            )
            """
        )
        params.append(account_code.strip())
    sql = f"""
        SELECT e.* FROM entries e
        WHERE {' AND '.join(clauses)}
        ORDER BY e.entry_date DESC, e.id DESC
    """
    if limit:
        sql += " LIMIT ?"
        params.append(int(limit))
    entries = [dict(row) for row in conn.execute(sql, params).fetchall()]
    if not entries:
        return []
    ids = [entry["id"] for entry in entries]
    placeholders = ",".join("?" for _ in ids)
    line_rows = conn.execute(
        f"""
        SELECT l.*, a.code AS account_code, a.name_fr, a.name_de, a.name_ru,
               an.code AS analytic_code, an.name_fr AS an_fr, an.name_de AS an_de, an.name_ru AS an_ru
        FROM lines l
        JOIN accounts a ON a.id = l.account_id
        LEFT JOIN analytics an ON an.id = l.analytic_id
        WHERE l.entry_id IN ({placeholders})
        ORDER BY l.id
        """,
        ids,
    ).fetchall()
    by_entry = {entry["id"]: [] for entry in entries}
    for line in line_rows:
        by_entry[line["entry_id"]].append(line)
    result = []
    for entry in entries:
        lines = by_entry[entry["id"]]
        debits = []
        credits = []
        total = 0
        for line in lines:
            item = _journal_line(line, sec)
            if line["side"] == "debit":
                debits.append(item)
                total += line["amount_cents"]
            else:
                credits.append(item)
        entry["debits"] = debits
        entry["credits"] = credits
        entry["amount"] = total
        result.append(entry)
    return result


def _journal_line(line, sec):
    sub = ""
    if sec == "ru":
        sub = line["name_ru"] or ""
    elif sec == "de":
        sub = line["name_de"] or ""
    analytic = ""
    analytic_sub = ""
    if line["analytic_id"]:
        code = line["analytic_code"] or ""
        name = line["an_fr"] or ""
        analytic = name if code.lower() == name.lower() else f"{code} · {name}"
        if sec == "ru":
            analytic_sub = line["an_ru"] or ""
        elif sec == "de":
            analytic_sub = line["an_de"] or ""
    return {
        "account_id": line["account_id"],
        "code": line["account_code"],
        "name_fr": line["name_fr"],
        "sub": sub,
        "analytic_id": line["analytic_id"] or 0,
        "analytic": analytic,
        "analytic_sub": analytic_sub,
        "amount": line["amount_cents"],
    }


def account_ledger(conn, account, year, sec, analytic_filter):
    """analytic_filter: None = tout, 0 = sans analytique, sinon l'id."""
    start = f"{year:04d}-01-01"
    end = f"{year:04d}-12-31"
    before_params = [account["id"], start]
    before_sql = """
        SELECT COALESCE(SUM(CASE WHEN l.side = 'debit' THEN l.amount_cents ELSE 0 END), 0) AS d,
               COALESCE(SUM(CASE WHEN l.side = 'credit' THEN l.amount_cents ELSE 0 END), 0) AS c
        FROM lines l
        JOIN entries e ON e.id = l.entry_id
        WHERE l.account_id = ? AND e.entry_date < ?
    """
    if analytic_filter is not None:
        before_sql += " AND COALESCE(l.analytic_id, 0) = ?"
        before_params.append(analytic_filter)
    before = conn.execute(before_sql, before_params).fetchone()
    opening = before["d"] - before["c"]
    line_params = [account["id"], start, end]
    line_sql = """
        SELECT e.id AS entry_id, e.entry_date, e.piece, e.label,
               l.id AS line_id, l.side, l.amount_cents, l.analytic_id,
               an.code AS analytic_code, an.name_fr AS an_fr, an.name_de AS an_de, an.name_ru AS an_ru
        FROM lines l
        JOIN entries e ON e.id = l.entry_id
        LEFT JOIN analytics an ON an.id = l.analytic_id
        WHERE l.account_id = ? AND e.entry_date BETWEEN ? AND ?
    """
    if analytic_filter is not None:
        line_sql += " AND COALESCE(l.analytic_id, 0) = ?"
        line_params.append(analytic_filter)
    line_sql += " ORDER BY e.entry_date, e.id, l.id"
    movements = [dict(row) for row in conn.execute(line_sql, line_params).fetchall()]
    entry_ids = sorted({row["entry_id"] for row in movements})
    counterparts = {}
    if entry_ids:
        placeholders = ",".join("?" for _ in entry_ids)
        others = conn.execute(
            f"""
            SELECT l.entry_id, l.id AS line_id, l.account_id, l.side, a.code, a.name_fr,
                   an.code AS analytic_code, an.name_fr AS an_fr
            FROM lines l
            JOIN accounts a ON a.id = l.account_id
            LEFT JOIN analytics an ON an.id = l.analytic_id
            WHERE l.entry_id IN ({placeholders})
            ORDER BY l.id
            """,
            entry_ids,
        ).fetchall()
        for row in others:
            counterparts.setdefault(row["entry_id"], []).append(row)
    running = opening
    lines = []
    for movement in movements:
        if movement["side"] == "debit":
            running += movement["amount_cents"]
            debit = movement["amount_cents"]
            credit = 0
        else:
            running -= movement["amount_cents"]
            debit = 0
            credit = movement["amount_cents"]
        others = [
            row
            for row in counterparts.get(movement["entry_id"], [])
            if row["line_id"] != movement["line_id"]
        ]
        if len(others) == 1:
            other = others[0]
            contra = f"{other['code']} {other['name_fr']}"
            if other["an_fr"]:
                contra += f" · {other['analytic_code']}"
            compound = False
        elif others:
            contra = ", ".join(row["code"] for row in others)
            compound = True
        else:
            contra = ""
            compound = False
        analytic = ""
        analytic_sub = ""
        if movement["analytic_id"]:
            code = movement["analytic_code"] or ""
            name = movement["an_fr"] or ""
            analytic = name if code.lower() == name.lower() else f"{code} · {name}"
            if sec == "ru":
                analytic_sub = movement["an_ru"] or ""
            elif sec == "de":
                analytic_sub = movement["an_de"] or ""
        lines.append(
            {
                "entry_id": movement["entry_id"],
                "date": movement["entry_date"],
                "piece": movement["piece"],
                "label": movement["label"],
                "debit": debit,
                "credit": credit,
                "balance": running,
                "contra": contra,
                "compound": compound,
                "analytic": analytic,
                "analytic_sub": analytic_sub,
                "analytic_id": movement["analytic_id"] or 0,
            }
        )
    return {"opening": opening, "lines": lines, "closing": running}


def account_groups(accounts, sec):
    groups = []
    for account in accounts:
        digit = account["code"][0]
        if not groups or groups[-1]["digit"] != digit:
            groups.append(
                {
                    "digit": digit,
                    "label": f"{digit} · {bundle('class_' + digit, sec)}",
                    "accounts": [],
                }
            )
        groups[-1]["accounts"].append(account)
    return groups


def decorate_account(account, sec):
    item = dict(account)
    item["sub"] = secondary_name(account, sec)
    item["label"] = f"{account['code']} · {account['name_fr']}"
    if item["sub"]:
        item["label"] += f" · {item['sub']}"
    return item


def decorate_analytic(analytic, sec):
    item = dict(analytic)
    item["sub"] = secondary_name(analytic, sec)
    if analytic["code"].lower() == analytic["name_fr"].lower():
        item["label"] = analytic["name_fr"]
    else:
        item["label"] = f"{analytic['code']} · {analytic['name_fr']}"
    if item["sub"]:
        item["label"] += f" · {item['sub']}"
    return item


def parse_entry_form(form, accounts_by_id, analytics_by_id):
    """Retourne meta, lignes prêtes à enregistrer, clés d'erreur, lignes brutes."""
    errors = []

    def add(key):
        if key not in errors:
            errors.append(key)

    parsed_date = parse_date(form.get("entry_date") or "")
    if parsed_date is None:
        add("err_date")
    label = (form.get("label") or "").strip()
    if not label:
        add("err_label")
    elif len(label) > 500:
        add("err_label_long")
    piece = (form.get("piece") or "").strip()
    if len(piece) > 40:
        add("err_piece_long")
    account_ids = form.getlist("account_id")
    analytic_ids = form.getlist("analytic_id")
    sides = form.getlist("side")
    line_amounts = form.getlist("line_amount")
    header_raw = str(form.get("amount") or "").strip()
    try:
        header_cents = parse_money(header_raw) or 0
    except MoneyError:
        add("err_money")
        header_cents = 0
    count = max(len(account_ids), len(analytic_ids), len(sides), len(line_amounts), 0)
    if count > 40:
        add("err_too_many_lines")
        count = 40

    def at(values, index):
        if index < len(values):
            return values[index]
        return ""

    raw_lines = []
    clean = []
    for index in range(count):
        account_raw = str(at(account_ids, index)).strip()
        analytic_raw = str(at(analytic_ids, index)).strip()
        side = str(at(sides, index)).strip()
        amount_raw = str(at(line_amounts, index)).strip()
        if side not in ("debit", "credit"):
            add("err_side")
            side = "debit"
        try:
            own_cents = parse_money(amount_raw) if amount_raw else None
        except MoneyError:
            add("err_money")
            own_cents = None
        if amount_raw:
            cents = own_cents or 0
        else:
            cents = header_cents
        raw_lines.append(
            {
                "account_id": account_raw,
                "analytic_id": analytic_raw,
                "side": side,
                "amount": amount_raw,
            }
        )
        if not account_raw and cents == 0 and not amount_raw:
            continue
        if not account_raw:
            add("err_account")
            continue
        if cents == 0:
            add("err_amount")
            continue
        try:
            account_id = int(account_raw)
        except ValueError:
            add("err_account")
            continue
        account = accounts_by_id.get(account_id)
        if account is None:
            add("err_account_missing")
            continue
        analytic_id = None
        if analytic_raw:
            try:
                analytic_id = int(analytic_raw)
            except ValueError:
                add("err_analytic")
                continue
            analytic = analytics_by_id.get(analytic_id)
            if analytic is None or analytic["account_id"] != account_id:
                add("err_analytic")
                continue
        else:
            active_analytics = [
                item
                for item in analytics_by_id.values()
                if item["account_id"] == account_id and item["active"]
            ]
            if account["analytics_required"] and active_analytics:
                add("err_required_analytic")
                continue
        clean.append(
            {
                "account_id": account_id,
                "analytic_id": analytic_id,
                "side": side,
                "amount_cents": cents,
            }
        )
    debit_total = sum(line["amount_cents"] for line in clean if line["side"] == "debit")
    credit_total = sum(line["amount_cents"] for line in clean if line["side"] == "credit")
    if not any(line["side"] == "debit" for line in clean) or not any(
        line["side"] == "credit" for line in clean
    ):
        add("err_lines")
    elif debit_total != credit_total or debit_total == 0:
        add("err_balance")
    while len(raw_lines) < 2:
        raw_lines.append(
            {
                "account_id": "",
                "analytic_id": "",
                "side": "credit" if raw_lines else "debit",
                "amount": "",
            }
        )
    if any(line["amount"] for line in raw_lines) and header_raw:
        for line in raw_lines:
            if not line["amount"] and line["account_id"]:
                line["amount"] = header_raw
    meta = {
        "entry_date": parsed_date.isoformat() if parsed_date else (form.get("entry_date") or ""),
        "piece": piece,
        "label": label,
        "amount": header_raw,
        "compound": any(line["amount"] for line in raw_lines),
        "debit_total": debit_total,
        "credit_total": credit_total,
    }
    if errors:
        clean = []
    return meta, clean, errors, raw_lines


def blank_lines(piece, entry_date):
    return {
        "meta": {
            "entry_date": entry_date,
            "piece": piece,
            "label": "",
            "amount": "",
            "compound": False,
            "debit_total": 0,
            "credit_total": 0,
        },
        "lines": [
            {"account_id": "", "analytic_id": "", "side": "debit", "amount": ""},
            {"account_id": "", "analytic_id": "", "side": "credit", "amount": ""},
        ],
        "errors": [],
    }


def lines_from_entry(entry, stored_lines):
    amounts = {line["amount_cents"] for line in stored_lines}
    compound = len(amounts) > 1
    shared = plain_money(stored_lines[0]["amount_cents"]) if stored_lines and not compound else ""
    raw = []
    for line in stored_lines:
        raw.append(
            {
                "account_id": str(line["account_id"]),
                "analytic_id": str(line["analytic_id"] or ""),
                "side": line["side"],
                "amount": plain_money(line["amount_cents"]) if compound else "",
            }
        )
    while len(raw) < 2:
        raw.append(
            {
                "account_id": "",
                "analytic_id": "",
                "side": "credit" if raw else "debit",
                "amount": "",
            }
        )
    meta = {
        "entry_date": entry["entry_date"],
        "piece": entry["piece"],
        "label": entry["label"],
        "amount": shared,
        "compound": compound,
        "debit_total": sum(line["amount_cents"] for line in stored_lines if line["side"] == "debit"),
        "credit_total": sum(line["amount_cents"] for line in stored_lines if line["side"] == "credit"),
    }
    return meta, raw


def clean_text(value, limit):
    text = (value or "").strip()
    if len(text) > limit:
        return None
    return text


def validate_account_fields(form, conn, ignore_id=None):
    errors = []
    code = (form.get("code") or "").strip()
    if not CODE_RE.fullmatch(code):
        errors.append("err_code")
    elif code_taken_safe(conn, code, ignore_id):
        errors.append("err_code_exists")
    name_fr = clean_text(form.get("name_fr"), 200)
    name_de = clean_text(form.get("name_de"), 200)
    name_ru = clean_text(form.get("name_ru"), 200)
    if name_fr is None or name_de is None or name_ru is None:
        errors.append("err_name_long")
    if name_fr == "":
        errors.append("err_name")
    statement = (form.get("statement") or "").strip()
    if statement not in STATEMENTS:
        errors.append("err_statement")
    fields = {
        "code": code,
        "name_fr": name_fr or "",
        "name_de": name_de or "",
        "name_ru": name_ru or "",
        "statement": statement if statement in STATEMENTS else "asset",
        "analytics_required": 1 if form.get("analytics_required") == "1" else 0,
        "is_vat": 1 if form.get("is_vat") == "1" else 0,
        "active": 1 if form.get("active") == "1" else 0,
    }
    return fields, errors


def code_taken_safe(conn, code, ignore_id):
    from app.db import code_taken

    return code_taken(conn, code, ignore_id)


def validate_analytic_fields(form, conn, account_id, ignore_id=None):
    from app.db import analytic_code_taken

    errors = []
    code = (form.get("code") or "").strip()
    if not ANALYTIC_CODE_RE.fullmatch(code):
        errors.append("err_analytic_code")
    elif analytic_code_taken(conn, account_id, code, ignore_id):
        errors.append("err_analytic_exists")
    name_fr = clean_text(form.get("name_fr"), 200)
    name_de = clean_text(form.get("name_de"), 200)
    name_ru = clean_text(form.get("name_ru"), 200)
    if name_fr is None or name_de is None or name_ru is None:
        errors.append("err_name_long")
    if name_fr == "":
        errors.append("err_analytic_name")
    fields = {
        "code": code,
        "name_fr": name_fr or "",
        "name_de": name_de or "",
        "name_ru": name_ru or "",
        "active": 1 if form.get("active") == "1" else 0,
    }
    return fields, errors


def report_title_keys():
    keys = set()
    for _, _, key in ASSET_GROUPS + LIABILITY_GROUPS + EQUITY_GROUPS:
        keys.add(key)
    for key, _, _, checkpoint in PL_SEQUENCE:
        keys.add(key)
        if checkpoint:
            keys.add(checkpoint)
    keys.update({"result_year", "result_prior", "closing_section", "class_1", "class_2", "class_3", "class_4", "class_5", "class_6", "class_7", "class_8", "class_9"})
    return keys


def titles_exist():
    missing = [key for key in report_title_keys() if key not in STRINGS]
    return missing
