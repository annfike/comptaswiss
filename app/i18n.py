"""Textes de l'interface. Le français est la langue principale."""

from markupsafe import Markup


def S(fr, de, ru):
    return {"fr": fr, "de": de, "ru": ru}


STRINGS = {
    "dashboard": S("Tableau de bord", "Übersicht", "Обзор"),
    "journal": S("Journal", "Journal", "Журнал"),
    "new_entry": S("Nouvelle écriture", "Neue Buchung", "Новая проводка"),
    "chart": S("Plan comptable", "Kontenplan", "План счетов"),
    "trial": S("Balance de sommes et soldes", "Summen- und Saldenliste", "Оборотно-сальдовая ведомость"),
    "balance_sheet": S("Bilan", "Bilanz", "Баланс"),
    "income": S("Compte de résultat", "Erfolgsrechnung", "Отчёт о прибылях и убытках"),
    "ledger": S("Fiche de compte", "Kontenblatt", "Карточка счёта"),
    "settings": S("Paramètres", "Einstellungen", "Настройки"),
    "year": S("Exercice", "Geschäftsjahr", "Год"),
    "translation": S("Traduction", "Übersetzung", "Перевод"),
    "russian": S("Russe", "Russisch", "Русский"),
    "german": S("Allemand", "Deutsch", "Немецкий"),
    "hide_translation": S("Masquer", "Ausblenden", "Скрыть"),
    "company_name": S("Raison sociale", "Firmenname", "Название фирмы"),
    "company_hint": S(
        "Affichée en tête des rapports.",
        "Erscheint im Kopf der Berichte.",
        "Показывается в шапке отчётов.",
    ),
    "save": S("Enregistrer", "Speichern", "Сохранить"),
    "cancel": S("Annuler", "Abbrechen", "Отмена"),
    "delete": S("Supprimer", "Löschen", "Удалить"),
    "edit": S("Modifier", "Bearbeiten", "Изменить"),
    "add": S("Ajouter", "Hinzufügen", "Добавить"),
    "active": S("Actif", "Aktiv", "Активен"),
    "inactive": S("Inactif", "Inaktiv", "Неактивен"),
    "code": S("Numéro", "Nummer", "Номер"),
    "name_fr": S("Nom français", "Französischer Name", "Название на французском"),
    "name_de": S("Nom allemand", "Deutscher Name", "Название на немецком"),
    "name_ru": S("Nom russe", "Russischer Name", "Название на русском"),
    "statement": S("Type de compte", "Kontoart", "Тип счёта"),
    "statement_help": S(
        "Proposé d'après le numéro. Vous pouvez le changer : il décide si le compte va au bilan ou au compte de résultat.",
        "Wird aus der Nummer vorgeschlagen. Sie können sie ändern: davon hängt Bilanz oder Erfolgsrechnung ab.",
        "Подставляется по номеру. Его можно сменить: от этого зависит, попадёт счёт в баланс или в отчёт о прибылях.",
    ),
    "asset": S("Actif", "Aktiv", "Актив"),
    "liability": S("Capitaux étrangers", "Fremdkapital", "Обязательство"),
    "equity": S("Capitaux propres", "Eigenkapital", "Капитал"),
    "pl": S("Compte de résultat", "Erfolgskonto", "Счёт результата"),
    "closing": S("Clôture", "Abschluss", "Закрытие"),
    "analytics": S("Analytiques", "Unterkonten", "Аналитика"),
    "analytic": S("Analytique", "Unterkonto", "Аналитика"),
    "analytics_required": S("Analytique obligatoire", "Unterkonto obligatorisch", "Аналитика обязательна"),
    "analytic_code": S("Code", "Code", "Код"),
    "analytic_code_help": S(
        "Court et stable, par exemple UBS ou PF.",
        "Kurz und stabil, zum Beispiel UBS oder PF.",
        "Короткий и постоянный, например UBS или PF.",
    ),
    "add_analytic": S("Ajouter une analytique", "Unterkonto hinzufügen", "Добавить аналитику"),
    "no_analytic": S("Aucune analytique pour l'instant.", "Noch kein Unterkonto.", "Аналитики пока нет."),
    "debit": S("Débit", "Soll", "Дебет"),
    "credit": S("Crédit", "Haben", "Кредит"),
    "amount": S("Montant", "Betrag", "Сумма"),
    "side": S("Sens", "Seite", "Сторона"),
    "actions": S("Actions", "Aktionen", "Действия"),
    "account": S("Compte", "Konto", "Счёт"),
    "date": S("Date", "Datum", "Дата"),
    "piece": S("Pièce", "Beleg", "Документ"),
    "label_field": S("Libellé", "Buchungstext", "Описание"),
    "search": S("Texte", "Text", "Текст"),
    "apply": S("Afficher", "Anzeigen", "Показать"),
    "print": S("Imprimer", "Drucken", "Печать"),
    "add_line": S("Ajouter une ligne", "Zeile hinzufügen", "Добавить строку"),
    "remove_line": S("Retirer", "Entfernen", "Убрать"),
    "save_entry": S("Enregistrer l'écriture", "Buchung speichern", "Сохранить проводку"),
    "edit_entry": S("Modifier l'écriture", "Buchung bearbeiten", "Изменить проводку"),
    "opening_dr": S("Solde initial D", "Anfangssaldo Soll", "Сальдо начальное дебет"),
    "opening_cr": S("Solde initial C", "Anfangssaldo Haben", "Сальдо начальное кредит"),
    "turnover_dr": S("Débit", "Soll", "Оборот дебет"),
    "turnover_cr": S("Crédit", "Haben", "Оборот кредит"),
    "closing_dr": S("Solde D", "Saldo Soll", "Сальдо конечное дебет"),
    "closing_cr": S("Solde C", "Saldo Haben", "Сальдо конечное кредит"),
    "total": S("Total", "Total", "Итого"),
    "by_analytic": S("Détail par analytique", "Details je Unterkonto", "Детализация по аналитике"),
    "sans_analytic": S("Sans analytique", "Ohne Unterkonto", "Без аналитики"),
    "all_analytics": S("Toutes les analytiques", "Alle Unterkonten", "Вся аналитика"),
    "assets": S("Actifs", "Aktiven", "Активы"),
    "liabilities_title": S("Capitaux étrangers", "Fremdkapital", "Обязательства"),
    "equity_title": S("Capitaux propres", "Eigenkapital", "Собственный капитал"),
    "total_assets": S("Total actifs", "Total Aktiven", "Итого активы"),
    "total_liabilities": S("Total passifs", "Total Passiven", "Итого пассивы"),
    "result_year": S("Résultat de l'exercice", "Jahresergebnis", "Результат года"),
    "result_prior": S(
        "Résultats des exercices précédents non affectés",
        "Nicht zugewiesene Ergebnisse früherer Jahre",
        "Нераспределённый результат прошлых лет",
    ),
    "closing_section": S("Comptes de clôture", "Abschlusskonten", "Счета закрытия"),
    "balanced_ok": S("Bilan équilibré", "Bilanz ausgeglichen", "Баланс сходится"),
    "difference": S("Écart", "Differenz", "Расхождение"),
    "class_1": S("Actifs", "Aktiven", "Активы"),
    "class_2": S("Passifs", "Passiven", "Пассивы"),
    "class_3": S("Produits", "Erträge", "Доходы"),
    "class_4": S(
        "Charges de matériel et de marchandises",
        "Material- und Warenaufwand",
        "Материальные затраты и товары",
    ),
    "class_5": S("Charges de personnel", "Personalaufwand", "Расходы на персонал"),
    "class_6": S(
        "Autres charges, amortissements et résultat financier",
        "Übriger Aufwand, Abschreibungen und Finanzergebnis",
        "Прочие расходы, амортизация и финансовый результат",
    ),
    "class_7": S("Résultat accessoire", "Betrieblicher Nebenerfolg", "Побочный результат"),
    "class_8": S(
        "Hors exploitation, extraordinaire et impôts",
        "Betriebsfremd, ausserordentlich und Steuern",
        "Внереализационные, чрезвычайные и налоги",
    ),
    "class_9": S("Clôture", "Abschluss", "Закрытие"),
    "g_cash": S("Liquidités", "Flüssige Mittel", "Денежные средства"),
    "g_receivables": S("Créances", "Forderungen", "Дебиторская задолженность"),
    "g_inventory": S("Stocks", "Vorräte", "Запасы"),
    "g_prepaid": S("Actifs transitoires", "Aktive Rechnungsabgrenzungen", "Активные переходящие остатки"),
    "g_financial_assets": S("Immobilisations financières", "Finanzanlagen", "Финансовые вложения"),
    "g_movables": S("Immobilisations corporelles meubles", "Mobile Sachanlagen", "Движимое имущество"),
    "g_property": S("Immeubles", "Immobilien", "Недвижимость"),
    "g_intangible": S("Immobilisations incorporelles", "Immaterielle Anlagen", "Нематериальные активы"),
    "g_other_assets": S("Autres actifs", "Übrige Aktiven", "Прочие активы"),
    "g_payables": S(
        "Dettes fournisseurs et acomptes",
        "Verbindlichkeiten und Anzahlungen",
        "Поставщики и авансы",
    ),
    "g_st_debt": S(
        "Dettes financières à court terme",
        "Kurzfristige Finanzverbindlichkeiten",
        "Краткосрочные финансовые обязательства",
    ),
    "g_other_st": S(
        "Autres dettes à court terme",
        "Übrige kurzfristige Verbindlichkeiten",
        "Прочие краткосрочные обязательства",
    ),
    "g_accruals": S(
        "Passifs transitoires et provisions à court terme",
        "Passive Abgrenzungen und kurzfristige Rückstellungen",
        "Пассивные переходящие и краткосрочные резервы",
    ),
    "g_lt_debt": S("Dettes à long terme", "Langfristige Verbindlichkeiten", "Долгосрочные обязательства"),
    "g_provisions": S("Provisions à long terme", "Langfristige Rückstellungen", "Долгосрочные резервы"),
    "g_other_liab": S("Autres capitaux étrangers", "Übriges Fremdkapital", "Прочие обязательства"),
    "g_capital": S("Capital", "Kapital", "Капитал"),
    "g_reserves": S(
        "Réserves et résultat reporté",
        "Reserven und Ergebnisvortrag",
        "Резервы и перенесённый результат",
    ),
    "g_other_equity": S("Autres capitaux propres", "Übriges Eigenkapital", "Прочий капитал"),
    "g_revenue": S("Produits nets", "Nettoerlöse", "Выручка"),
    "g_cogs": S(
        "Charges de matériel, marchandises et prestations",
        "Material-, Waren- und Dienstleistungsaufwand",
        "Материальные затраты и закупки",
    ),
    "g_staff": S("Charges de personnel", "Personalaufwand", "Расходы на персонал"),
    "g_opex": S("Autres charges d'exploitation", "Übriger Betriebsaufwand", "Прочие операционные расходы"),
    "g_depr": S("Amortissements", "Abschreibungen", "Амортизация"),
    "g_financial": S("Résultat financier", "Finanzergebnis", "Финансовый результат"),
    "g_ancillary": S("Résultat accessoire", "Betrieblicher Nebenerfolg", "Побочный результат"),
    "g_extraordinary": S(
        "Résultat hors exploitation et extraordinaire",
        "Betriebsfremder und ausserordentlicher Erfolg",
        "Внереализационный и чрезвычайный результат",
    ),
    "g_pl_other": S("Autres comptes de résultat", "Übrige Erfolgskonten", "Прочие счета результата"),
    "g_tax": S("Impôts directs", "Direkte Steuern", "Прямые налоги"),
    "sub_margin": S("Marge brute", "Bruttogewinn", "Валовая прибыль"),
    "sub_operating": S("Résultat d'exploitation", "Betriebsergebnis", "Операционный результат"),
    "sub_before_tax": S("Résultat avant impôts", "Ergebnis vor Steuern", "Результат до налогов"),
    "empty_journal": S(
        "Aucune écriture sur cet exercice.",
        "Keine Buchungen in diesem Geschäftsjahr.",
        "В этом году проводок нет.",
    ),
    "empty_report": S(
        "Aucun mouvement sur cet exercice.",
        "Keine Bewegungen in diesem Geschäftsjahr.",
        "В этом году движений нет.",
    ),
    "empty_income": S(
        "Aucun produit ni charge sur cet exercice.",
        "Keine Erträge oder Aufwände in diesem Geschäftsjahr.",
        "В этом году нет доходов и расходов.",
    ),
    "entries_count": S("écritures", "Buchungen", "проводок"),
    "recent": S("Dernières écritures", "Letzte Buchungen", "Последние проводки"),
    "home_result": S("Résultat", "Ergebnis", "Результат"),
    "intro_title": S("Pour commencer", "So fangen Sie an", "С чего начать"),
    "step1": S(
        "Vérifiez le plan comptable. Sur 1020 Banques, ajoutez une analytique par établissement si vous en avez plusieurs.",
        "Prüfen Sie den Kontenplan. Auf 1020 Bankguthaben je Institut ein Unterkonto anlegen, wenn Sie mehrere haben.",
        "Проверьте план счетов. На 1020 Банки заведите аналитику по каждому банку, если их несколько.",
    ),
    "step3": S(
        "Enregistrez les écritures du quotidien. Journal, balance, bilan et compte de résultat se calculent à partir de là.",
        "Erfassen Sie die laufenden Buchungen. Journal, Saldoliste, Bilanz und Erfolgsrechnung rechnen sich daraus.",
        "Вводите ежедневные проводки. Журнал, оборотка, баланс и отчёт о прибылях считаются из них.",
    ),
    "dashboard_hint": S(
        "Les rapports se calculent depuis le journal. Rien n'est saisi deux fois.",
        "Die Berichte werden aus dem Journal berechnet. Nichts wird doppelt erfasst.",
        "Отчёты считаются из журнала. Ничего не вводится дважды.",
    ),
    "new_account": S("Nouveau compte", "Neues Konto", "Новый счёт"),
    "edit_account": S("Modifier le compte", "Konto bearbeiten", "Изменить счёт"),
    "plan_intro": S(
        "Plan comptable PME (Kontenrahmen KMU). Vous pouvez ajouter, renommer ou désactiver des comptes.",
        "Kontenrahmen KMU. Konten können ergänzt, umbenannt oder deaktiviert werden.",
        "Стандартный план счетов KMU. Счета можно добавлять, переименовывать и отключать.",
    ),
    "example_banks": S(
        "Exemple : sur 1020 Banques, une analytique par établissement (UBS, PostFinance, Raiffeisen). Cochez « analytique obligatoire » pour exiger ce choix dans chaque écriture.",
        "Beispiel: auf 1020 Bankguthaben je Institut ein Unterkonto (UBS, PostFinance, Raiffeisen). « Unterkonto obligatorisch » erzwingt die Auswahl in jeder Buchung.",
        "Пример: на 1020 Банки — аналитика по каждому банку (UBS, PostFinance, Raiffeisen). Отметьте « аналитика обязательна », чтобы без неё проводка не сохранялась.",
    ),
    "capital_note": S(
        "2800 est le capital social (Sàrl, SA) ou le capital propre (raison individuelle). 2850 est le compte privé de l'exploitant. 2970 reçoit le résultat des années précédentes si vous le transférez.",
        "2800 ist das Stammkapital (GmbH, AG) oder das Eigenkapital (Einzelunternehmen). 2850 ist das Privatkonto. 2970 nimmt das Ergebnis früherer Jahre auf, wenn Sie es übertragen.",
        "2800 — уставный капитал (Sàrl, SA) или собственный капитал индивидуального предприятия. 2850 — личный счёт. 2970 — результат прошлых лет, если вы его перенесли.",
    ),
    "close_year_note": S(
        "Le résultat de l'exercice est calculé à partir des comptes 3 à 8. Pour l'affecter au capital, passez une écriture au 31.12 qui solde ces comptes et crédite 2970 ou 2800. Sans cette écriture, il reste affiché ici, et l'année suivante dans la ligne des résultats précédents.",
        "Das Jahresergebnis wird aus den Konten 3 bis 8 berechnet. Um es dem Kapital zuzuweisen, buchen Sie am 31.12 diese Konten aus und erkennen 2970 oder 2800. Sonst bleibt es hier stehen und im Folgejahr bei den früheren Ergebnissen.",
        "Результат года считается по счетам 3–8. Чтобы перенести его в капитал, сделайте проводку на 31.12: закройте эти счета и отнесите остаток на 2970 или 2800. Если проводки нет, результат остаётся в этой строке, а в следующем году показывается как нераспределённый результат прошлых лет.",
    ),
    "vat": S("TVA", "MWST", "НДС"),
    "vat_future": S(
        "La TVA n'est pas encore calculée. Les comptes 1170, 1171, 2200 et 2201 sont déjà dans le plan : vous pouvez les utiliser à la main. Le calcul automatique viendra plus tard.",
        "Die MWST wird noch nicht berechnet. Die Konten 1170, 1171, 2200 und 2201 sind bereits im Kontenplan und können manuell bebucht werden. Die automatische Berechnung folgt später.",
        "НДС пока не рассчитывается. Счета 1170, 1171, 2200 и 2201 уже есть в плане: их можно использовать вручную. Автоматический расчёт появится позже.",
    ),
    "settings_intro": S(
        "L'interface reste en français. Le russe ou l'allemand s'affiche en petit en dessous.",
        "Die Oberfläche bleibt Französisch. Russisch oder Deutsch erscheint klein darunter.",
        "Интерфейс остаётся французским. Русский или немецкий показывается мелким шрифтом ниже.",
    ),
    "show_inactive": S(
        "Afficher les comptes inactifs",
        "Inaktive Konten anzeigen",
        "Показать неактивные счета",
    ),
    "filter_chart": S("Filtrer le plan", "Kontenplan filtern", "Фильтр плана счетов"),
    "status": S("Statut", "Status", "Статус"),
    "active_account": S("Compte actif", "Konto aktiv", "Счёт активен"),
    "back_chart": S("Retour au plan", "Zurück zum Kontenplan", "К плану счетов"),
    "back_journal": S("Retour au journal", "Zurück zum Journal", "К журналу"),
    "confirm_delete_entry": S(
        "Supprimer cette écriture ?",
        "Diese Buchung löschen?",
        "Удалить эту проводку?",
    ),
    "confirm_delete_account": S(
        "Supprimer ce compte ?",
        "Dieses Konto löschen?",
        "Удалить этот счёт?",
    ),
    "confirm_delete_analytic": S(
        "Supprimer cette analytique ?",
        "Dieses Unterkonto löschen?",
        "Удалить эту аналитику?",
    ),
    "saved": S("Écriture enregistrée.", "Buchung gespeichert.", "Проводка сохранена."),
    "deleted": S("Écriture supprimée.", "Buchung gelöscht.", "Проводка удалена."),
    "account_saved": S("Compte enregistré.", "Konto gespeichert.", "Счёт сохранён."),
    "account_deleted": S("Compte supprimé.", "Konto gelöscht.", "Счёт удалён."),
    "analytic_saved": S("Analytique enregistrée.", "Unterkonto gespeichert.", "Аналитика сохранена."),
    "analytic_deleted": S("Analytique supprimée.", "Unterkonto gelöscht.", "Аналитика удалена."),
    "settings_saved": S("Paramètres enregistrés.", "Einstellungen gespeichert.", "Настройки сохранены."),
    "err_date": S("Date invalide.", "Ungültiges Datum.", "Неверная дата."),
    "err_label": S("Le libellé est obligatoire.", "Der Buchungstext ist erforderlich.", "Укажите описание проводки."),
    "err_label_long": S("Le libellé est trop long.", "Der Buchungstext ist zu lang.", "Слишком длинное описание."),
    "err_piece_long": S("Le numéro de pièce est trop long.", "Die Belegnummer ist zu lang.", "Слишком длинный номер документа."),
    "err_balance": S(
        "Le total du débit et le total du crédit ne sont pas égaux.",
        "Die Summe Soll und die Summe Haben sind nicht gleich.",
        "Итог дебета и итог кредита не равны.",
    ),
    "err_lines": S(
        "Ajoutez au moins une ligne au débit et une ligne au crédit.",
        "Mindestens eine Sollzeile und eine Habenzeile.",
        "Нужна хотя бы одна строка по дебету и одна по кредиту.",
    ),
    "err_money": S(
        "Montant illisible. Utilisez 1234.50 ou 1234,50.",
        "Betrag nicht lesbar. Verwenden Sie 1234.50 oder 1234,50.",
        "Сумма не распознана. Используйте 1234.50 или 1234,50.",
    ),
    "err_account": S(
        "Chaque montant doit avoir un compte.",
        "Jeder Betrag braucht ein Konto.",
        "Для каждой суммы нужен счёт.",
    ),
    "err_amount": S(
        "Indiquez le montant de l'écriture.",
        "Geben Sie den Betrag der Buchung an.",
        "Укажите сумму проводки.",
    ),
    "err_side": S(
        "Chaque ligne doit être au débit ou au crédit.",
        "Jede Zeile muss Soll oder Haben sein.",
        "Каждая строка должна быть по дебету или по кредиту.",
    ),
    "err_both": S(
        "Une ligne ne peut pas être à la fois au débit et au crédit.",
        "Eine Zeile kann nicht gleichzeitig Soll und Haben sein.",
        "В одной строке нельзя заполнять и дебет, и кредит.",
    ),
    "err_analytic": S(
        "L'analytique ne correspond pas au compte.",
        "Das Unterkonto gehört nicht zu diesem Konto.",
        "Аналитика не относится к этому счёту.",
    ),
    "err_required_analytic": S(
        "Ce compte exige une analytique.",
        "Dieses Konto verlangt ein Unterkonto.",
        "Для этого счёта аналитика обязательна.",
    ),
    "err_code": S(
        "Le numéro de compte doit comporter 3 à 8 chiffres, sans zéro devant.",
        "Die Kontonummer muss 3 bis 8 Ziffern haben, ohne führende Null.",
        "Номер счёта: от 3 до 8 цифр, без нуля впереди.",
    ),
    "err_code_exists": S(
        "Ce numéro de compte existe déjà.",
        "Diese Kontonummer gibt es bereits.",
        "Такой номер счёта уже есть.",
    ),
    "err_name": S(
        "Le nom français est obligatoire.",
        "Der französische Name ist erforderlich.",
        "Французское название обязательно.",
    ),
    "err_name_long": S("Le nom est trop long.", "Der Name ist zu lang.", "Слишком длинное название."),
    "err_used": S(
        "Ce compte a déjà des écritures : désactivez-le au lieu de le supprimer.",
        "Dieses Konto hat Buchungen: deaktivieren Sie es, statt es zu löschen.",
        "На счёте уже есть проводки: отключите его, а не удаляйте.",
    ),
    "err_analytic_used": S(
        "Cette analytique a déjà des écritures.",
        "Dieses Unterkonto hat Buchungen.",
        "На этой аналитике уже есть проводки.",
    ),
    "err_analytic_code": S(
        "Indiquez un code court : lettres, chiffres, point, tiret ou souligné.",
        "Geben Sie einen kurzen Code an: Buchstaben, Ziffern, Punkt, Bindestrich oder Unterstrich.",
        "Укажите короткий код: буквы, цифры, точка, дефис или подчёркивание.",
    ),
    "err_analytic_name": S(
        "Le nom français de l'analytique est obligatoire.",
        "Der französische Name des Unterkontos ist erforderlich.",
        "Французское название аналитики обязательно.",
    ),
    "err_analytic_exists": S(
        "Ce code analytique existe déjà sur le compte.",
        "Dieser Unterkonto-Code existiert auf dem Konto bereits.",
        "Такой код аналитики на счёте уже есть.",
    ),
    "err_network": S(
        "Enregistrement impossible.",
        "Speichern nicht möglich.",
        "Не удалось сохранить.",
    ),
    "err_statement": S("Type de compte inconnu.", "Unbekannte Kontoart.", "Неизвестный тип счёта."),
    "err_too_many_lines": S(
        "Trop de lignes : 40 au maximum.",
        "Zu viele Zeilen: höchstens 40.",
        "Слишком много строк: не больше 40.",
    ),
    "err_account_missing": S("Compte introuvable.", "Konto nicht gefunden.", "Счёт не найден."),
    "not_found_page": S("Page introuvable.", "Seite nicht gefunden.", "Страница не найдена."),
    "opening_balance": S("Solde avant l'exercice", "Saldo vor dem Geschäftsjahr", "Сальдо до начала года"),
    "closing_balance": S("Solde final", "Schlusssaldo", "Конечное сальдо"),
    "counterpart": S("Contrepartie", "Gegenkonto", "Корреспонденция"),
    "compound": S("Écriture composée", "Sammelbuchung", "Сложная проводка"),
    "no_lines_account": S(
        "Aucune écriture sur ce compte pour cet exercice.",
        "Keine Buchungen auf diesem Konto in diesem Geschäftsjahr.",
        "По этому счёту в этом году проводок нет.",
    ),
    "ledger_note": S(
        "Le solde ci-dessus est cumulé. Le compte de résultat ne retient que les écritures de l'exercice.",
        "Der Saldo oben ist kumuliert. Die Erfolgsrechnung enthält nur die Buchungen des Geschäftsjahres.",
        "Сальдо выше — накопительное. В отчёт о прибылях попадают только проводки выбранного года.",
    ),
    "analytics_after_save": S(
        "Enregistrez d'abord le compte, puis ajoutez les analytiques.",
        "Speichern Sie zuerst das Konto, dann die Unterkonten.",
        "Сначала сохраните счёт, затем добавьте аналитику.",
    ),
    "data_file": S("Fichier des données", "Datendatei", "Файл данных"),
    "backup_hint": S(
        "Copiez ce fichier pour sauvegarder la comptabilité. Fermez d'abord la fenêtre noire du programme.",
        "Kopieren Sie diese Datei als Sicherung. Schliessen Sie vorher das schwarze Fenster des Programms.",
        "Скопируйте этот файл, чтобы сохранить бухгалтерию. Сначала закройте чёрное окно программы.",
    ),
    "stop_hint": S(
        "Pour arrêter le programme, fermez la fenêtre noire ouverte par start.bat.",
        "Zum Beenden das schwarze Fenster von start.bat schliessen.",
        "Чтобы остановить программу, закройте чёрное окно, открытое через start.bat.",
    ),
    "compte_filter": S("Numéro de compte", "Kontonummer", "Номер счёта"),
    "vat_account": S("Compte de TVA", "MWST-Konto", "Счёт НДС"),
    "vat_account_help": S(
        "Réservé pour la TVA. Pas encore de calcul automatique.",
        "Für die MWST vorgesehen. Noch ohne automatische Berechnung.",
        "Заготовлен для НДС. Автоматического расчёта пока нет.",
    ),
    "choose": S("Choisir", "Wählen", "Выбрать"),
    "filter_account": S("Filtrer", "Filtern", "Фильтр"),
    "yes": S("Oui", "Ja", "Да"),
    "no": S("Non", "Nein", "Нет"),
}


FLASH = {
    "saved",
    "deleted",
    "account_saved",
    "account_deleted",
    "analytic_saved",
    "analytic_deleted",
    "settings_saved",
}


def t(key, sec):
    item = STRINGS[key]
    other = item[sec] if sec in ("ru", "de") else ""
    if other:
        return Markup('{}<span class="sub">{}</span>').format(item["fr"], other)
    return Markup.escape(item["fr"])


def tf(key):
    return STRINGS[key]["fr"]


def tconfirm(key, sec):
    item = STRINGS[key]
    if sec in ("ru", "de") and item[sec]:
        return Markup("{}&#10;{}").format(item["fr"], item[sec])
    return Markup.escape(item["fr"])


def bundle(key, sec):
    item = STRINGS[key]
    if sec in ("ru", "de") and item[sec]:
        return item["fr"] + " · " + item[sec]
    return item["fr"]


def secondary_name(row, sec):
    if sec == "ru":
        return row["name_ru"] or ""
    if sec == "de":
        return row["name_de"] or ""
    return ""
