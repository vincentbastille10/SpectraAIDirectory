# app.py — Spectra AI Directory
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
)
import stripe

# =========================
# CONFIG FLASK & STRIPE
# =========================

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

DB_PATH = os.getenv("DB_PATH", "annuaire.db")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # prix à 20€ créé dans Stripe

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY manquant dans le .env")

if not STRIPE_PRICE_ID:
    raise RuntimeError("STRIPE_PRICE_ID manquant dans le .env")

stripe.api_key = STRIPE_SECRET_KEY


# =========================
# BDD SQLITE
# =========================

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
                url TEXT NOT NULL,
                short_description TEXT,
                long_description TEXT,
                logo_url TEXT,
                category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_published INTEGER NOT NULL DEFAULT 0
            );
            """
        )


# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    # quelques derniers outils publiés pour la page d’accueil
    with get_db() as db:
        tools = db.execute(
            """
            SELECT id, name, url, short_description, logo_url, category, tags
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC
            LIMIT 6;
            """
        ).fetchall()
    return render_template("index.html", tools=tools)


@app.route("/annuaire")
def annuaire_list():
    with get_db() as db:
        tools = db.execute(
            """
            SELECT id, name, url, short_description, logo_url, category, tags
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC;
            """
        ).fetchall()
    return render_template("annuaire_list.html", tools=tools)


@app.route("/tool/<int:tool_id>")
def tool_detail(tool_id: int):
    with get_db() as db:
        tool = db.execute(
            """
            SELECT *
            FROM tools
            WHERE id = ? AND is_published = 1;
            """,
            (tool_id,),
        ).fetchone()

    if tool is None:
        abort(404)

    return render_template("tool_detail.html", tool=tool)


# -------- AJOUT D’UN OUTIL (FORM + STRIPE) --------

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_tool():
    if request.method == "GET":
        # simple formulaire
        return render_template("ajouter.html")

    # POST : on reçoit les infos + on crée la session Stripe
    name = request.form.get("name", "").strip()
    url_site = request.form.get("url", "").strip()
    short_description = request.form.get("short_description", "").strip()
    long_description = request.form.get("long_description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    category = request.form.get("category", "").strip()
    tags = request.form.get("tags", "").strip()

    if not name or not url_site:
        # minimum vital
        return "Le nom et l’URL de l’outil sont obligatoires.", 400

    created_at = datetime.utcnow().isoformat()

    # 1) on enregistre d’abord l’outil en BDD comme "non publié"
    with get_db() as db:
        cur = db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0);
            """,
            (
                name,
                url_site,
                short_description,
                long_description,
                logo_url,
                category,
                tags,
                created_at,
            ),
        )
        tool_id = cur.lastrowid

    # 2) on crée la session Stripe Checkout à 20€
    try:
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            success_url=(
                url_for("checkout_success", _external=True)
                + "?session_id={CHECKOUT_SESSION_ID}"
                + f"&tool_id={tool_id}"
            ),
            cancel_url=(
                url_for("checkout_cancel", _external=True)
                + f"?tool_id={tool_id}"
            ),
        )
    except Exception as e:
        # si Stripe plante, on supprime l’outil en attente
        with get_db() as db:
            db.execute("DELETE FROM tools WHERE id = ?;", (tool_id,))
        return f"Erreur Stripe : {e}", 500

    # 3) on redirige vers la page de paiement Stripe
    return redirect(checkout_session.url, code=303)


# -------- RETOUR STRIPE --------

@app.route("/checkout_success")
def checkout_success():
    session_id = request.args.get("session_id")
    tool_id = request.args.get("tool_id")

    if not session_id or not tool_id:
        return "Paramètres manquants.", 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return f"Erreur Stripe lors de la vérification : {e}", 500

    # On s’assure que le paiement est bien réalisé
    if session.get("payment_status") != "paid":
        return "Paiement non validé.", 400

    # On publie la fiche dans l’annuaire
    with get_db() as db:
        db.execute(
            "UPDATE tools SET is_published = 1 WHERE id = ?;",
            (tool_id,),
        )

    return render_template("checkout_success.html")


@app.route("/checkout_cancel")
def checkout_cancel():
    # ici, on peut éventuellement supprimer la fiche non payée
    tool_id = request.args.get("tool_id")
    if tool_id:
        with get_db() as db:
            db.execute("DELETE FROM tools WHERE id = ? AND is_published = 0;", (tool_id,))
    return "Paiement annulé. Votre outil n’a pas été publié."


# =========================
# LANCEMENT
# =========================

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
