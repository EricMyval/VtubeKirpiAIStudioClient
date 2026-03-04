import json
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.utils.currency_converter import CurrencyConverter

bp = Blueprint(
    "currencies",
    __name__,
    url_prefix="/admin/currencies"
)

RATES_FILE = Path("data/db/currency_rates.json")


@bp.route("/", methods=["GET"])
def currencies_page():
    rates = CurrencyConverter.get_rates()
    return render_template(
        "currencies.html",
        rates=rates
    )


@bp.route("/save", methods=["POST"])
def save_currencies():
    new_rates: dict[str, float] = {}

    for code, value in request.form.items():
        try:
            new_rates[code.upper()] = float(value)
        except ValueError:
            flash(f"Неверное значение для {code}", "danger")
            return redirect(url_for("currencies.currencies_page"))

    # защита от выстрела в ногу
    if "RUB" not in new_rates or new_rates["RUB"] != 1:
        flash("RUB должен существовать и быть равен 1", "danger")
        return redirect(url_for("currencies.currencies_page"))

    RATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RATES_FILE, "w", encoding="utf-8") as f:
        json.dump(new_rates, f, ensure_ascii=False, indent=2)

    CurrencyConverter.reload()
    flash("Курсы валют сохранены", "success")

    return redirect(url_for("currencies.currencies_page"))
