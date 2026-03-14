from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import database as db
import api

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user_id():
    return session["user_id"]


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        if not username or not password:
            flash("Username and password are required.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif not db.create_user(username, password):
            flash("Username already taken.", "error")
        else:
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.verify_password(username, password)

        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── App routes ────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    movements = db.get_all_movements(current_user_id())
    return render_template("index.html", movimientos=movements, active="index")


@app.route("/purchase", methods=["GET", "POST"])
@login_required
def purchase():
    result    = None
    form_data = {}
    uid       = current_user_id()
    balances  = {c: db.get_balance(c, uid) for c in api.CURRENCIES if c != "EUR"}

    if request.method == "POST":
        action          = request.form.get("action")
        from_currency   = request.form.get("moneda_from", "")
        to_currency     = request.form.get("moneda_to", "")
        from_amount_str = request.form.get("cantidad_from", "")

        form_data = {
            "moneda_from": from_currency,
            "moneda_to":   to_currency,
            "cantidad_from": from_amount_str,
        }

        try:
            from_amount = float(from_amount_str)
            if from_amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid amount greater than 0.", "error")
            return render_template("purchase.html", monedas=api.CURRENCIES,
                                   active="purchase", form_data=form_data,
                                   balances=balances)

        if from_currency == to_currency:
            flash("Source and destination currencies must be different.", "error")
            return render_template("purchase.html", monedas=api.CURRENCIES,
                                   active="purchase", form_data=form_data,
                                   balances=balances)

        if from_currency != "EUR":
            balance = db.get_balance(from_currency, uid)
            if from_amount > balance:
                flash(
                    f"Insufficient balance. You have {balance:.6f} {from_currency} available.",
                    "error"
                )
                return render_template("purchase.html", monedas=api.CURRENCIES,
                                       active="purchase", form_data=form_data,
                                       balances=balances)

        if action == "calcular":
            try:
                to_amount = api.convert_price(from_amount, from_currency, to_currency)
                result    = round(to_amount, 8)
                form_data["cantidad_to"] = result
            except Exception as e:
                flash(f"API error: {e}", "error")

        elif action == "aceptar":
            try:
                to_amount = float(request.form.get("cantidad_to", ""))
            except ValueError:
                flash("You must calculate the value before confirming.", "error")
                return render_template("purchase.html", monedas=api.CURRENCIES,
                                       active="purchase", form_data=form_data,
                                       balances=balances)

            now = datetime.now()
            db.insert_movement(
                user_id=uid,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                from_currency=from_currency,
                from_amount=from_amount,
                to_currency=to_currency,
                to_amount=to_amount,
            )
            flash("Movement recorded successfully.", "success")
            return redirect(url_for("index"))

    return render_template("purchase.html", monedas=api.CURRENCIES,
                           active="purchase", form_data=form_data,
                           resultado=result, balances=balances)


@app.route("/status")
@login_required
def status():
    uid = current_user_id()
    invested, recovered, balances = db.get_status_data(uid)
    purchase_value = invested - recovered

    current_value  = 0.0
    balances_in_eur = {}
    api_error = None

    try:
        for crypto, amount in balances.items():
            price_eur = api.get_price_in_eur(crypto, amount)
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


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
