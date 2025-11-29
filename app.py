from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, g
)
from werkzeug.middleware.proxy_fix import ProxyFix

# Stripe (optionnel mais prêt à l'emploi)
import stripe

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "annuaire.db"

# --------- APP ----------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Pour que Flask comprenne les en-têtes quand tu es derrière un proxy (Render, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

# --------- STRIPE ----------
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")  # prix unique 20€
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def stripe_enabled() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and STRIPE_PUBLIC_KEY)


# --------- DB ----------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tagline TEXT,
                description TEXT,
                website_url TEXT NOT NULL,
                contact_email TEXT,
                category TEXT,
                country TEXT,
                logo_url TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


@app.before_request
def before_request():
    # S'assure que la base existe
    if not DB_PATH.exists():
        init_db()
    g.stripe_enabled = stripe_enabled()
    g.STRIPE_PUBLIC_KEY = STRIPE_PUBLIC_KEY


# --------- ROUTES ----------
@app.route("/")
def index():
    with get_db() as db:
        tools = db.execute(
            "SELECT * FROM tools ORDER BY datetime(created_at) DESC LIMIT 12"
        ).fetchall()
    return render_template("index.html", tools=tools)


@app.route("/annuaire")
def annuaire():
    category = request.args.get("categorie") or ""
    with get_db() as db:
        if category:
            tools = db.execute(
                "SELECT * FROM tools WHERE category = ? ORDER BY datetime(created_at) DESC",
                (category,),
            ).fetchall()
        else:
            tools = db.execute(
                "SELECT * FROM tools ORDER BY datetime(created_at) DESC"
            ).fetchall()
    return render_template("annuaire_list.html", tools=tools, category=category)


@app.route("/tool/<int:tool_id>")
def tool_detail(tool_id: int):
    with get_db() as db:
        tool = db.execute(
            "SELECT * FROM tools WHERE id = ?", (tool_id,)
        ).fetchone()
    if not tool:
        flash("Outil introuvable.", "error")
        return redirect(url_for("annuaire"))
    return render_template("tool_detail.html", tool=tool)


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        tagline = request.form.get("tagline", "").strip()
        description = request.form.get("description", "").strip()
        website_url = request.form.get("website_url", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        category = request.form.get("category", "").strip()
        country = request.form.get("country", "").strip()
        logo_url = request.form.get("logo_url", "").strip()

        if not name or not website_url:
            flash("Le nom et l’URL du site sont obligatoires.", "error")
            return redirect(url_for("ajouter"))

        if stripe_enabled():
            # Création d'une session Stripe Checkout
            try:
                domain = request.url_root.rstrip("/")
                metadata = {
                    "name": name[:200],
                    "tagline": tagline[:200],
                    "description": description[:500],
                    "website_url": website_url[:200],
                    "contact_email": contact_email[:200],
                    "category": category[:100],
                    "country": country[:100],
                    "logo_url": logo_url[:300],
                }
                checkout_session = stripe.checkout.Session.create(
                    mode="payment",
                    line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
                    success_url=f"{domain}{url_for('checkout_success')}?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{domain}{url_for('checkout_cancel')}",
                    metadata=metadata,
                )
                return redirect(checkout_session.url, code=303)
            except Exception as e:
                print("Erreur Stripe:", e)
                flash("Erreur lors de la création du paiement. Mode démo activé.", "error")

        # Si Stripe désactivé ou erreur → MODE DEMO : on enregistre directement
        created_at = datetime.utcnow().isoformat()
        with get_db() as db:
            db.execute(
                """
                INSERT INTO tools
                    (name, tagline, description, website_url, contact_email,
                     category, country, logo_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, tagline, description, website_url, contact_email,
                 category, country, logo_url, created_at),
            )
        flash("Merci ! Votre outil a été ajouté (MODE DÉMO, aucun paiement effectué).", "success")
        return redirect(url_for("annuaire"))

    return render_template("ajouter.html")


@app.route("/checkout/success")
def checkout_success():
    session_id = request.args.get("session_id")
    if not session_id or not stripe_enabled():
        flash("Session de paiement introuvable. Votre outil peut ne pas avoir été enregistré.", "error")
        return redirect(url_for("index"))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        print("Erreur Stripe retrieve:", e)
        flash("Impossible de vérifier le paiement.", "error")
        return redirect(url_for("index"))

    if checkout_session.payment_status != "paid":
        flash("Le paiement n’a pas été confirmé.", "error")
        return redirect(url_for("index"))

    metadata = checkout_session.metadata or {}
    name = metadata.get("name", "").strip()
    website_url = metadata.get("website_url", "").strip()

    if not name or not website_url:
        flash("Les données de l’outil sont incomplètes.", "error")
        return redirect(url_for("index"))

    tagline = metadata.get("tagline", "")
    description = metadata.get("description", "")
    contact_email = metadata.get("contact_email", "")
    category = metadata.get("category", "")
    country = metadata.get("country", "")
    logo_url = metadata.get("logo_url", "")

    created_at = datetime.utcnow().isoformat()
    with get_db() as db:
        db.execute(
            """
            INSERT INTO tools
                (name, tagline, description, website_url, contact_email,
                 category, country, logo_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, tagline, description, website_url, contact_email,
             category, country, logo_url, created_at),
        )
    flash("Merci ! Votre outil IA est maintenant listé dans l’annuaire.", "success")
    return render_template("checkout_success.html", tool_name=name)


@app.route("/checkout/cancel")
def checkout_cancel():
    flash("Paiement annulé. Votre outil n’a pas été ajouté.", "info")
    return redirect(url_for("ajouter"))


if __name__ == "__main__":
    # Lancement local
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
