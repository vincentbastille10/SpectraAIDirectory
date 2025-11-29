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
    Response,
)
import stripe


# ============================================================
# CONFIG FLASK & STRIPE
# ============================================================

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

DB_PATH = os.getenv("DB_PATH", "annuaire.db")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY manquant")
if not STRIPE_PRICE_ID:
    raise RuntimeError("STRIPE_PRICE_ID manquant")

stripe.api_key = STRIPE_SECRET_KEY


# ============================================================
# BDD SQLITE
# ============================================================

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def seed_tools(db: sqlite3.Connection):
    """Ajoute des outils IA crédibles s'il n'y en a aucun."""
    now = datetime.utcnow().isoformat()

    seeds = [
        {
            "name": "Betty Bots — Assistante IA métier",
            "url": "https://www.spectramedia.online/",
            "short": "Flotte d’assistantes IA spécialisées par métier qui qualifient vos leads.",
            "long": "Betty Bots est une flotte d’assistantes IA spécialisées par métier (artisan, restauration, esthétique…). "
                    "Elles répondent aux prospects, posent les bonnes questions et envoient tout par email.",
            "logo": "",
            "cat": "Assistant IA",
            "tags": "#leadgen #assistantIA",
        },
        {
            "name": "SalesPilot AI",
            "url": "https://example.com/salespilot",
            "short": "Relances commerciales et scoring automatique.",
            "long": "",
            "logo": "",
            "cat": "Sales Automation",
            "tags": "#sales",
        },
        {
            "name": "DocuSense IA",
            "url": "https://example.com/docusense",
            "short": "Posez des questions à vos PDF.",
            "long": "",
            "logo": "",
            "cat": "Knowledge",
            "tags": "#pdf #qa",
        },
        {
            "name": "SupportGenie AI",
            "url": "https://example.com/supportgenie",
            "short": "Support client IA 24/7.",
            "long": "",
            "logo": "",
            "cat": "Support",
            "tags": "#support",
        },
        {
            "name": "VideoScript Studio",
            "url": "https://example.com/videoscript",
            "short": "Scripts automatiques pour TikTok, YouTube.",
            "long": "",
            "logo": "",
            "cat": "Video",
            "tags": "#video #tiktok",
        },
        {
            "name": "DesignPrompt Pro",
            "url": "https://example.com/designprompt",
            "short": "Prompts prêts pour générer des visuels cohérents.",
            "long": "",
            "logo": "",
            "cat": "Design",
            "tags": "#prompt #design",
        },
        {
            "name": "CodeBuddy Autocomplete",
            "url": "https://example.com/codebuddy",
            "short": "Complétion de code IA.",
            "long": "",
            "logo": "",
            "cat": "Développement",
            "tags": "#dev",
        },
        {
            "name": "HRMatch IA",
            "url": "https://example.com/hrmatch",
            "short": "Filtre vos CV automatiquement.",
            "long": "",
            "logo": "",
            "cat": "RH",
            "tags": "#cv #rh",
        },
        {
            "name": "LegalDraft AI",
            "url": "https://example.com/legaldraft",
            "short": "Contrats générés automatiquement.",
            "long": "",
            "logo": "",
            "cat": "Légal",
            "tags": "#legal",
        },
        {
            "name": "EmailFlow Optimizer",
            "url": "https://example.com/emailflow",
            "short": "Optimisation IA des emails marketing.",
            "long": "",
            "logo": "",
            "cat": "Email",
            "tags": "#email",
        },
        {
            "name": "SocialBoost AI",
            "url": "https://example.com/socialboost",
            "short": "Posts automatiques adaptés aux réseaux.",
            "long": "",
            "logo": "",
            "cat": "Social Media",
            "tags": "#social",
        },
        {
            "name": "DataSense Analytics",
            "url": "https://example.com/datasense",
            "short": "Analyse vos ventes + signaux faibles.",
            "long": "",
            "logo": "",
            "cat": "Analytics",
            "tags": "#analytics",
        },
        {
            "name": "MeetingNotes AI",
            "url": "https://example.com/meetingnotes",
            "short": "Compte-rendu automatique de vos réunions.",
            "long": "",
            "logo": "",
            "cat": "Productivité",
            "tags": "#meetings",
        },
        {
            "name": "VoiceAssist Studio",
            "url": "https://example.com/voiceassist",
            "short": "Assistants vocaux IA pour hotline.",
            "long": "",
            "logo": "",
            "cat": "Voix",
            "tags": "#voice",
        },
        {
            "name": "EcomPricing IA",
            "url": "https://example.com/ecompricing",
            "short": "Optimisation automatique de prix e-commerce.",
            "long": "",
            "logo": "",
            "cat": "E-commerce",
            "tags": "#pricing",
        },
    ]

    for t in seeds:
        db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (t["name"], t["url"], t["short"], t["long"], t["logo"], t["cat"], t["tags"], now),
        )


def init_db():
    with get_db() as db:
        db.execute("""
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
        """)

        row = db.execute("SELECT COUNT(*) AS c FROM tools").fetchone()
        if row["c"] == 0:
            seed_tools(db)


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    with get_db() as db:
        tools = db.execute("""
            SELECT id, name, url, short_description, logo_url, category, tags
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC
            LIMIT 6;
        """).fetchall()
    return render_template("index.html", tools=tools)


@app.route("/annuaire")
def annuaire_list():
    with get_db() as db:
        tools = db.execute("""
            SELECT id, name, url, short_description, logo_url, category, tags
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC;
        """).fetchall()
    return render_template("annuaire_list.html", tools=tools)


@app.route("/tool/<int:tool_id>")
def tool_detail(tool_id):
    with get_db() as db:
        tool = db.execute("""
            SELECT *
            FROM tools
            WHERE id = ? AND is_published = 1
        """, (tool_id,)).fetchone()

    if not tool:
        abort(404)
    return render_template("tool_detail.html", tool=tool)


@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_tool():
    if request.method == "GET":
        return render_template("ajouter.html")

    name = request.form.get("name", "").strip()
    url_site = request.form.get("url", "").strip()
    short_desc = request.form.get("short_description", "").strip()
    long_desc = request.form.get("long_description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    category = request.form.get("category", "").strip()
    tags = request.form.get("tags", "").strip()

    if not name or not url_site:
        return "Nom + URL obligatoires", 400

    created_at = datetime.utcnow().isoformat()

    with get_db() as db:
        cur = db.execute("""
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (name, url_site, short_desc, long_desc, logo_url, category, tags, created_at))
        tool_id = cur.lastrowid

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=url_for("checkout_success", _external=True)
                        + f"?session_id={{CHECKOUT_SESSION_ID}}&tool_id={tool_id}",
            cancel_url=url_for("checkout_cancel", _external=True)
                       + f"?tool_id={tool_id}",
        )
    except Exception as e:
        with get_db() as db:
            db.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        return f"Erreur Stripe : {e}", 500

    return redirect(session.url, code=303)


@app.route("/checkout_success")
def checkout_success():
    session_id = request.args.get("session_id")
    tool_id = request.args.get("tool_id")

    if not session_id or not tool_id:
        return "Paramètres manquants", 400

    s = stripe.checkout.Session.retrieve(session_id)
    if s.get("payment_status") != "paid":
        return "Paiement non validé", 400

    with get_db() as db:
        db.execute("UPDATE tools SET is_published = 1 WHERE id = ?", (tool_id,))

    return render_template("checkout_success.html")


@app.route("/checkout_cancel")
def checkout_cancel():
    tool_id = request.args.get("tool_id")
    if tool_id:
        with get_db() as db:
            db.execute("DELETE FROM tools WHERE id = ? AND is_published = 0", (tool_id,))
    return "Paiement annulé."


# ============================================================
# GOOGLE SEARCH CONSOLE (fichier HTML)
# ============================================================

@app.route("/google8334646a4a411e97.html")
def google_verification():
    return "google-site-verification: google8334646a4a411e97.html"


# ============================================================
# ROBOTS.TXT + SITEMAP
# ============================================================

@app.route("/robots.txt")
def robots_txt():
    base = request.url_root.rstrip("/")
    text = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return Response(text, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    base = request.url_root.rstrip("/")

    urls = [
        {"loc": f"{base}/", "priority": "1.0"},
        {"loc": f"{base}/annuaire", "priority": "0.9"},
        {"loc": f"{base}/ajouter", "priority": "0.5"},
    ]

    with get_db() as db:
        tools = db.execute("""
            SELECT id, created_at
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC;
        """).fetchall()

    for t in tools:
        urls.append({
            "loc": f"{base}/tool/{t['id']}",
            "priority": "0.8",
            "lastmod": t["created_at"],
        })

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for u in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{u['loc']}</loc>")
        if "lastmod" in u:
            xml.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml.append(f"    <priority>{u['priority']}</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")


# ============================================================
# INIT AUTO
# ============================================================

with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
