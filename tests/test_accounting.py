import os
import re
import tempfile
import unittest
from pathlib import Path

from app.accounting import (
    balance_sheet,
    income_statement,
    parse_entry_form,
    parse_money,
    titles_exist,
    trial_balance,
    MoneyError,
    format_chf,
)
from app.chart import ACCOUNTS
from app.db import (
    connect,
    fetch_account_by_code,
    init_db,
    insert_account,
    insert_analytic,
    replace_entry,
    update_account,
)
from app.i18n import STRINGS


class FakeForm(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)

    def getlist(self, key):
        value = dict.get(self, key, [])
        if isinstance(value, list):
            return value
        return [value]


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("COMPTA_DB")
        handle, path = tempfile.mkstemp(suffix=".sqlite")
        os.close(handle)
        os.environ["COMPTA_DB"] = path
        self.path = path
        init_db()

    def tearDown(self):
        if self._old is None:
            os.environ.pop("COMPTA_DB", None)
        else:
            os.environ["COMPTA_DB"] = self._old
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(self.path + suffix)
            except OSError:
                pass

    def test_translations_and_chart(self):
        for key, value in STRINGS.items():
            self.assertTrue(value["fr"] and value["de"] and value["ru"], key)
        self.assertEqual(titles_exist(), [])
        codes = [row[0] for row in ACCOUNTS]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertIn("1020", codes)
        self.assertIn("2800", codes)
        self.assertIn("3400", codes)
        self.assertGreaterEqual(len(codes), 70)
        root = Path(__file__).resolve().parents[1] / "app" / "templates"
        used = set()
        for path in root.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            used.update(re.findall(r"[tf]\('([a-z0-9_]+)'", text))
            used.update(re.findall(r'tconfirm\(\'([a-z0-9_]+)\'', text))
        missing = sorted(key for key in used if key not in STRINGS)
        self.assertEqual(missing, [])

    def test_money(self):
        self.assertIsNone(parse_money(""))
        self.assertIsNone(parse_money("   "))
        self.assertEqual(parse_money("10"), 1000)
        self.assertEqual(parse_money("1'234.50"), 123450)
        self.assertEqual(parse_money("1 234,5"), 123450)
        self.assertEqual(parse_money("1.234,50"), 123450)
        self.assertEqual(parse_money("CHF 10.00"), 1000)
        self.assertEqual(parse_money("0.50"), 50)
        self.assertEqual(parse_money("10.999"), 1099900)
        self.assertEqual(format_chf(123456), "1'234.56")
        self.assertEqual(format_chf(-50), "-0.50")
        self.assertEqual(format_chf(0), "")
        self.assertEqual(format_chf(0, True), "0.00")
        with self.assertRaises(MoneyError):
            parse_money("-1")
        with self.assertRaises(MoneyError):
            parse_money("10.9999")
        with self.assertRaises(MoneyError):
            parse_money("abc")

    def test_books_balance_with_analytics_and_prior_year(self):
        with connect() as conn:
            bank = fetch_account_by_code(conn, "1020")["id"]
            capital = fetch_account_by_code(conn, "2800")["id"]
            expense = fetch_account_by_code(conn, "6500")["id"]
            revenue = fetch_account_by_code(conn, "3400")["id"]
            ubs = insert_analytic(conn, bank, {
                "code": "UBS", "name_fr": "UBS", "name_de": "UBS", "name_ru": "ЮБС", "active": 1,
            })
            postfinance = insert_analytic(conn, bank, {
                "code": "PF", "name_fr": "PostFinance", "name_de": "PostFinance", "name_ru": "Постфинанс", "active": 1,
            })
            replace_entry(conn, None, "2025-06-01", "1", "Facture 2025", [
                {"account_id": bank, "analytic_id": ubs, "side": "debit", "amount_cents": 5000},
                {"account_id": revenue, "analytic_id": None, "side": "credit", "amount_cents": 5000},
            ])
            replace_entry(conn, None, "2026-01-01", "1", "Apport", [
                {"account_id": bank, "analytic_id": ubs, "side": "debit", "amount_cents": 100000},
                {"account_id": capital, "analytic_id": None, "side": "credit", "amount_cents": 100000},
            ])
            replace_entry(conn, None, "2026-02-01", "2", "Loyer", [
                {"account_id": expense, "analytic_id": None, "side": "debit", "amount_cents": 20000},
                {"account_id": bank, "analytic_id": ubs, "side": "credit", "amount_cents": 20000},
            ])
            replace_entry(conn, None, "2026-03-01", "3", "Honoraires", [
                {"account_id": bank, "analytic_id": ubs, "side": "debit", "amount_cents": 80000},
                {"account_id": bank, "analytic_id": postfinance, "side": "debit", "amount_cents": 20000},
                {"account_id": revenue, "analytic_id": None, "side": "credit", "amount_cents": 100000},
            ])
            sheet = balance_sheet(conn, 2026, "ru")
            self.assertEqual(sheet["difference"], 0)
            self.assertEqual(sheet["total_assets"], 185000)
            self.assertEqual(sheet["result_year"], 80000)
            self.assertEqual(sheet["result_prior"], 5000)
            trial = trial_balance(conn, 2026, "ru", detail=True)
            self.assertTrue(trial["balanced"])
            bank_row = next(row for row in trial["rows"] if row["code"] == "1020")
            self.assertEqual(bank_row["ouv_d"], 5000)
            self.assertEqual(bank_row["mov_d"], 200000)
            self.assertEqual(bank_row["mov_c"], 20000)
            self.assertEqual(bank_row["sol_d"], 185000)
            by_code = {item["code"]: item for item in bank_row["analytics"] if not item["sans"]}
            self.assertEqual(by_code["UBS"]["ouv_d"], 5000)
            self.assertEqual(by_code["UBS"]["sol_d"], 165000)
            self.assertEqual(by_code["PF"]["mov_d"], 20000)
            self.assertEqual(income_statement(conn, 2026, "ru")["result"], 80000)
            self.assertEqual(income_statement(conn, 2025, "off")["result"], 5000)

    def test_required_analytic_and_added_account(self):
        with connect() as conn:
            bank = fetch_account_by_code(conn, "1020")
            capital = fetch_account_by_code(conn, "2800")
            update_account(conn, bank["id"], {
                "code": bank["code"],
                "name_fr": bank["name_fr"],
                "name_de": bank["name_de"],
                "name_ru": bank["name_ru"],
                "statement": bank["statement"],
                "analytics_required": 1,
                "is_vat": 0,
                "active": 1,
            })
            ubs = insert_analytic(conn, bank["id"], {
                "code": "UBS", "name_fr": "UBS", "name_de": "", "name_ru": "", "active": 1,
            })
            accounts = {row["id"]: row for row in conn.execute("SELECT * FROM accounts")}
            analytics = {row["id"]: row for row in conn.execute("SELECT * FROM analytics")}
            form = FakeForm({
                "entry_date": "2026-04-01",
                "piece": "9",
                "label": "Test",
                "account_id": [str(bank["id"]), str(capital["id"])],
                "analytic_id": ["", ""],
                "side": ["debit", "credit"],
                "amount": "10.00",
            })
            _meta, clean, errors, _raw = parse_entry_form(form, accounts, analytics)
            self.assertIn("err_required_analytic", errors)
            self.assertEqual(clean, [])
            form["analytic_id"] = [str(ubs), ""]
            accounts = {row["id"]: row for row in conn.execute("SELECT * FROM accounts")}
            _meta, clean, errors, _raw = parse_entry_form(form, accounts, analytics)
            self.assertNotIn("err_required_analytic", errors)
            self.assertEqual(len(clean), 2)
            self.assertEqual(clean[0]["amount_cents"], 1000)
            self.assertEqual(clean[1]["amount_cents"], 1000)
            self.assertEqual([line["side"] for line in clean], ["debit", "credit"])
            custom = insert_account(conn, {
                "code": "1990",
                "name_fr": "Compte propre",
                "name_de": "Eigenes Konto",
                "name_ru": "Свой счёт",
                "statement": "asset",
                "analytics_required": 0,
                "is_vat": 0,
                "active": 1,
            })
            replace_entry(conn, None, "2026-05-01", "4", "Apport", [
                {"account_id": custom, "analytic_id": None, "side": "debit", "amount_cents": 3000},
                {"account_id": capital["id"], "analytic_id": None, "side": "credit", "amount_cents": 3000},
            ])
            sheet = balance_sheet(conn, 2026, "de")
            self.assertEqual(sheet["difference"], 0)
            codes = [row["code"] for group in sheet["asset_groups"] for row in group["accounts"]]
            self.assertIn("1990", codes)

    def test_pages(self):
        try:
            from fastapi.testclient import TestClient
        except Exception as exc:
            self.skipTest(str(exc))
        from app.main import app

        with TestClient(app) as client:
            pages = {
                "/": "Tableau de bord",
                "/journal?year=2026": "Journal",
                "/plan?year=2026": "1020",
                "/ecritures/nouvelle?year=2026": "entry_date",
                "/balance?year=2026": "Balance de sommes et soldes",
                "/bilan?year=2026": "Actifs",
                "/resultat?year=2026": "Compte de résultat",
                "/parametres?year=2026": "Fichier des données",
            }
            for path, needle in pages.items():
                response = client.get(path)
                self.assertEqual(response.status_code, 200, path)
                self.assertIn(needle, response.text)
                if path.startswith("/ecritures/nouvelle"):
                    self.assertNotIn("Saisissez la somme une seule fois", response.text)
                    self.assertNotIn('id="totals"', response.text)
                    self.assertIn("add-analytic", response.text)
            bank = None
            capital = None
            with connect() as conn:
                bank = fetch_account_by_code(conn, "1020")["id"]
                capital = fetch_account_by_code(conn, "2800")["id"]
            saved = client.post("/ecritures", data={
                "year": "2026",
                "entry_date": "2026-01-15",
                "piece": "1",
                "label": "Apport",
                "account_id": [str(bank), str(capital)],
                "analytic_id": ["", ""],
                "side": ["debit", "credit"],
                "amount": "1500.00",
            }, follow_redirects=True)
            self.assertEqual(saved.status_code, 200)
            self.assertIn("Apport", saved.text)
            sheet = client.get("/bilan?year=2026")
            self.assertIn("1&#39;500.00", sheet.text)
            self.assertIn("Bilan équilibré", sheet.text)
            created = client.post("/ecritures/analytique", data={
                "account_id": str(bank),
                "code": "POSTE",
                "name_fr": "PostFinance",
                "name_ru": "Постфинанс",
            })
            self.assertEqual(created.status_code, 200)
            body = created.json()
            self.assertTrue(body["ok"])
            self.assertEqual(body["account_id"], bank)
            self.assertIn("PostFinance", body["label"])
            self.assertIn("Постфинанс", body["label"])
            again = client.get("/ecritures/nouvelle?year=2026")
            self.assertIn("PostFinance", again.text)
            duplicate = client.post("/ecritures/analytique", data={
                "account_id": str(bank),
                "code": "POSTE",
                "name_fr": "Encore",
            })
            self.assertEqual(duplicate.status_code, 400)
            self.assertFalse(duplicate.json()["ok"])
            unbalanced = client.post("/ecritures", data={
                "year": "2026",
                "entry_date": "2026-01-16",
                "piece": "2",
                "label": "Faux",
                "account_id": [str(bank), str(capital)],
                "analytic_id": ["", ""],
                "side": ["debit", "credit"],
                "line_amount": ["10.00", "4.00"],
            })
            self.assertEqual(unbalanced.status_code, 200)
            self.assertIn("ne sont pas égaux", unbalanced.text)


if __name__ == "__main__":
    unittest.main()
