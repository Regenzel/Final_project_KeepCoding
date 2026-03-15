from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import models.movement as movement_model
import services.crypto_api as crypto_api
from controllers import login_required

main_bp = Blueprint("main", __name__)


def current_user_id():
    return session["user_id"]


@main_bp.route("/")
@login_required
def index():
    movements = movement_model.get_all_movements(current_user_id())
    return render_template("index.html", movimientos=movements, active="index")


@main_bp.route("/purchase", methods=["GET", "POST"])
@login_required
def purchase():
    result    = None
    form_data = {}
    uid       = current_user_id()
    balances  = {c: movement_model.get_balance(c, uid) for c in crypto_api.CURRENCIES if c != "EUR"}

    if request.method == "POST":
        action          = request.form.get("action")
        from_currency   = request.form.get("moneda_from", "")
        to_currency     = request.form.get("moneda_to", "")
        from_amount_str = request.form.get("cantidad_from", "")

        form_data = {
            "moneda_from":   from_currency,
            "moneda_to":     to_currency,
            "cantidad_from": from_amount_str,
        }

        try:
            from_amount = float(from_amount_str)
            if from_amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid amount greater than 0.", "error")
            return render_template("purchase.html", monedas=crypto_api.CURRENCIES,
                                   active="purchase", form_data=form_data,
                                   resultado=None, balances=balances)

        if from_currency == to_currency:
            flash("Source and destination currencies must be different.", "error")
            return render_template("purchase.html", monedas=crypto_api.CURRENCIES,
                                   active="purchase", form_data=form_data,
                                   resultado=None, balances=balances)

        if from_currency != "EUR":
            balance = movement_model.get_balance(from_currency, uid)
            if from_amount > balance:
                flash(
                    f"Insufficient balance. You have {balance:.6f} {from_currency} available.",
                    "error"
                )
                return render_template("purchase.html", monedas=crypto_api.CURRENCIES,
                                       active="purchase", form_data=form_data,
                                       resultado=None, balances=balances)

        if action == "calcular":
            try:
                to_amount = crypto_api.convert_price(from_amount, from_currency, to_currency)
                result    = round(to_amount, 8)
                form_data["cantidad_to"] = result
            except Exception as e:
                flash(f"API error: {e}", "error")

        elif action == "aceptar":
            try:
                to_amount = float(request.form.get("cantidad_to", ""))
            except ValueError:
                flash("You must calculate the value before confirming.", "error")
                return render_template("purchase.html", monedas=crypto_api.CURRENCIES,
                                       active="purchase", form_data=form_data,
                                       resultado=None, balances=balances)

            now = datetime.now()
            movement_model.insert_movement(
                user_id=uid,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                from_currency=from_currency,
                from_amount=from_amount,
                to_currency=to_currency,
                to_amount=to_amount,
            )
            flash("Movement recorded successfully.", "success")
            return redirect(url_for("main.index"))

    return render_template("purchase.html", monedas=crypto_api.CURRENCIES,
                           active="purchase", form_data=form_data,
                           resultado=result, balances=balances)


@main_bp.route("/status")
@login_required
def status():
    uid = current_user_id()
    invested, recovered, balances = movement_model.get_status_data(uid)
    purchase_value = invested - recovered

    current_value   = 0.0
    balances_in_eur = {}
    api_error       = None

    try:
        for crypto, amount in balances.items():
            price_eur = crypto_api.get_price_in_eur(crypto, amount)
            balances_in_eur[crypto] = {"cantidad": amount, "valor_eur": price_eur}
            current_value += price_eur
    except Exception as e:
        api_error = str(e)

    gain_loss = current_value - purchase_value

    return render_template(
        "status.html",
        active="status",
        invertido=invested,
        recuperado=recovered,
        valor_compra=purchase_value,
        saldos_eur=balances_in_eur,
        valor_actual=current_value,
        ganancia=gain_loss,
        error_api=api_error,
    )
