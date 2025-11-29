# app.py — Spectra AI Directory (Stripe + SEO + sitemap + seed d'outils)
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


# =========================
# CONFIG FLASK & STRIPE
# =========================

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


# =========================
# BASE DE DONNÉES SQLITE
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


def seed_tools(db: sqlite3.Connection) -> None:
    """Pré-remplit l'annuaire avec quelques outils IA crédibles (dont Betty Bots)."""
    now = datetime.utcnow().isoformat()

    tools = [
        # 1 — Betty Bots (ton produit)
        {
            "name": "Betty Bots — Assistante IA métier",
            "url": "https://www.spectramedia.online/",
            "short": "Flotte d’assistantes IA qui qualifient vos leads et envoient les demandes directement dans votre boîte mail.",
            "long": (
                "Betty Bots est une flotte d’assistantes IA spécialisées par métier "
                "(artisan, restaurateur, esthétique, médical, immobilier…). "
                "Chaque Betty répond comme une vraie assistante humaine, pose les bonnes questions, "
                "qualifie les prospects et envoie des emails prêts à traiter. "
                "Pensé pour les TPE/PME qui n’ont pas le temps de répondre à tous les messages."
            ),
            "logo": "",
            "category": "Assistant IA / Lead gen",
            "tags": "#leads #PME #assistantIA",
        },
        # 2
        {
            "name": "SalesPilot AI",
            "url": "https://example.com/salespilot-ai",
            "short": "Copilote IA pour relances commerciales automatiques et scoring de prospects.",
            "long": "",
            "logo": "",
            "category": "Sales Automation",
            "tags": "#sales #crm #automation",
        },
        # 3
        {
            "name": "DocuSense IA",
            "url": "https://example.com/docusense",
            "short": "Moteur de questions / réponses sur vos PDF, contrats et procédures.",
            "long": "",
            "logo": "",
            "category": "Knowledge Base",
            "tags": "#documentation #qa #pdf",
        },
        # 4
        {
            "name": "SupportGenie AI",
            "url": "https://example.com/supportgenie",
            "short": "Chat de support client IA qui répond 24/7 à partir de votre base de connaissances.",
            "long": "",
            "logo": "",
            "category": "Support Client",
            "tags": "#support #saas #helpdesk",
        },
        # 5
        {
            "name": "VideoScript Studio",
            "url": "https://example.com/videoscript-studio",
            "short": "Générateur de scripts vidéo pour TikTok, YouTube et Reels.",
            "long": "",
            "logo": "",
            "category": "Contenu / Vidéo",
            "tags": "#tiktok #youtube #scripts",
        },
        # 6
        {
            "name": "DesignPrompt Pro",
            "url": "https://example.com/designprompt-pro",
            "short": "Prompts prêts à l’emploi pour générer des visuels cohérents avec votre marque.",
            "long": "",
            "logo": "",
            "category": "Design / Création",
            "tags": "#design #image #prompt",
        },
        # 7
        {
            "name": "CodeBuddy Autocomplete",
            "url": "https://example.com/codebuddy",
            "short": "Assistant IA de complétion de code pour accélérer le développement.",
            "long": "",
            "logo": "",
            "category": "Dev / Code",
            "tags": "#dev #autocomplete #code",
        },
        # 8
        {
            "name": "HRMatch IA",
            "url": "https://example.com/hrmatch",
            "short": "Filtre les CV et propose une short-list de candidats automatiquement.",
            "long": "",
            "logo": "",
            "category": "RH / Recrutement",
            "tags": "#rh #recrutement #cv",
        },
        # 9
        {
            "name": "LegalDraft AI",
            "url": "https://example.com/legaldraft",
            "short": "Assistance à la rédaction de contrats et courriers juridiques.",
            "long": "",
            "logo": "",
            "category": "Légal",
            "tags": "#legal #contrats #juridique",
        },
        # 10
        {
            "name": "EmailFlow Optimizer",
            "url": "https://example.com/emailflow",
            "short": "Optimisation automatique de vos séquences d’emails marketing.",
            "long": "",
            "logo": "",
            "category": "Emailing",
            "tags": "#email #marketing #automation",
        },
        # 11
        {
            "name": "SocialBoost AI",
            "url": "https://example.com/socialboost",
            "short": "Propose des posts adaptés à chaque réseau social, avec visuels suggérés.",
            "long": "",
            "logo": "",
            "category": "Social Media",
            "tags": "#socialmedia #content #growth",
        },
        # 12
        {
            "name": "DataSense Analytics",
            "url": "https://example.com/datasense",
            "short": "Analyse vos ventes et détecte les signaux faibles avec l’IA.",
            "long": "",
            "logo": "",
            "category": "Analytics",
            "tags": "#data #analytics #insights",
        },
        # 13
        {
            "name": "MeetingNotes AI",
            "url": "https://example.com/meetingnotes",
            "short": "Transcrit vos réunions et envoie un compte rendu structuré.",
            "long": "",
            "logo": "",
            "category": "Productivité",
            "tags": "#meetings #notes #productivity",
        },
        # 14
        {
            "name": "VoiceAssist Studio",
            "url": "https://example.com/voiceassist",
            "short": "Crée des assistants vocaux IA pour hotline et standard téléphonique.",
            "long": "",
            "logo": "",
            "category": "Voix / Téléphonie",
            "tags": "#voice #ivr #assistant",
        },
        # 15
        {
            "name": "EcomPricing AI",
            "url": "https://example.com/ecompricing",
            "short": "Optimise automatiquement les prix de vos produits e-commerce.",
            "long": "",
            "logo": "",
            "category": "E-commerce",
            "tags": "#ecommerce #pricing #roi",
        },
    ]

    for t in tools:
        db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                t["name"],
                t["url"],
                t["short"],
                t["long"],
                t["logo"],
                t["category"],
                t["tags"],
                now,
            ),
        )


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

        # Si la table est vide, on pré-remplit avec quelques outils
        row = db.execute("SELECT COUNT(*) AS c FROM tools").fetchone()
        if row["c"] == 0:
            seed_tools(db)


# =========================
# ROUTES PRINCIPALES
# =========================

@app.route("/")
def index():
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

    if not tool:
        abort(404)

    return render_template("tool_detail.html", tool=tool)


# =========================
# AJOUT + STRIPE
# =========================

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_tool():
    if request.method == "GET":
        return render_template("ajouter.html")

    name = request.form.get("name", "").strip()
    url_site = request.form.get("url", "").strip()
    short_description = request.form.get("short_description", "").strip()
    long_description = request.form.get("long_description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    category = request.form.get("category", "").strip()
    tags = request.form.get("tags", "").strip()

    if not name or not url_site:
        return "Nom + URL obligatoires", 400

    created_at = datetime.utcnow().isoformat()

    with get_db() as db:
        cur = db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                + f"?session_id={{CHECKOUT_SESSION_ID}}&tool_id={tool_id}"
            ),
            cancel_url=(
                url_for("checkout_cancel", _external=True)
                + f"?tool_id={tool_id}"
            ),
        )
    except Exception as e:
        with get_db() as db:
            db.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        return f"Erreur Stripe : {e}", 500

    return redirect(checkout_session.url, code=303)


@app.route("/checkout_success")
def checkout_success():
    session_id = request.args.get("session_id")
    tool_id = request.args.get("tool_id")

    if not session_id or not tool_id:
        return "Paramètres manquants", 400

    session = stripe.checkout.Session.retrieve(session_id)

    if session.get("payment_status") != "paid":
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


# =========================
# SITEMAP & ROBOTS
# =========================

@app.route("/robots.txt")
def robots_txt():
    base = request.url_root.rstrip("/")
    txt = f"""User-agent: *
Allow: /
Sitemap: {base}/sitemap.xml
"""
    return Response(txt, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    base = request.url_root.rstrip("/")

    urls = [
        {"loc": f"{base}/", "priority": "1.0"},
        {"loc": f"{base}/annuaire", "priority": "0.9"},
        {"loc": f"{base}/ajouter", "priority": "0.5"},
    ]

    with get_db() as db:
        tools = db.execute(
            """
            SELECT id, created_at
            FROM tools
            WHERE is_published = 1
            ORDER BY id DESC;
            """
        ).fetchall()

    for t in tools:
        urls.append(
            {
                "loc": f"{base}/tool/{t['id']}",
                "priority": "0.8",
                "lastmod": t["created_at"],
            }
        )

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for u in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{u['loc']}</loc>")
        if u.get("lastmod"):
            xml.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml.append(f"    <priority>{u['priority']}</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")


# =========================
# INIT DB AU DÉMARRAGE
# =========================

with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
