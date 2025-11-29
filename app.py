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
    send_from_directory,
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


def seed_tools(db: sqlite3.Connection) -> None:
    """Seed initial d'outils IA (avec logos en /public)."""
    now = datetime.utcnow().isoformat()
    base_url = "https://www.spectramedia.online/"

    seeds = [
        {
            "name": "Betty Bots — Assistante IA métier",
            "url": base_url,
            "short": "Flotte d’assistantes IA spécialisées par métier qui qualifient vos leads automatiquement.",
            "long": (
                "Betty Bots est une flotte d’assistantes IA spécialisées par métier "
                "(artisan, restauration, esthétique, médical, immobilier…). "
                "Chaque Betty répond comme une vraie assistante humaine, pose les bonnes questions, "
                "qualifie les prospects et envoie des emails prêts à traiter."
            ),
            "logo": "/public/_f130dd3e-bc09-4582-a9ce-bbb32c733795.jpeg",
            "cat": "Assistant IA / Lead gen",
            "tags": "#leads #PME #assistantIA",
        },
        {
            "name": "SalesPilot AI",
            "url": base_url + "?from=annuaire&tool=salespilot",
            "short": "Relances commerciales automatiques et scoring de prospects.",
            "long": "",
            "logo": "/public/_70fec99c-ebc7-4189-945a-c366afbfa70b.jpeg",
            "cat": "Sales Automation",
            "tags": "#sales #crm #automation",
        },
        {
            "name": "DocuSense IA",
            "url": base_url + "?from=annuaire&tool=docusense",
            "short": "Posez des questions à vos PDF, contrats et procédures internes.",
            "long": "",
            "logo": "/public/_b50d4099-f147-4466-89d1-73016026c012.jpeg",
            "cat": "Knowledge Base",
            "tags": "#documentation #pdf #qa",
        },
        {
            "name": "SupportGenie AI",
            "url": base_url + "?from=annuaire&tool=supportgenie",
            "short": "Chat de support client IA disponible 24/7.",
            "long": "",
            "logo": "/public/_ec0203d3-9974-4f19-ab27-8961569ac101.jpeg",
            "cat": "Support Client",
            "tags": "#support #saas #helpdesk",
        },
        {
            "name": "VideoScript Studio",
            "url": base_url + "?from=annuaire&tool=videoscript",
            "short": "Génère des scripts pour TikTok, Reels et YouTube en quelques secondes.",
            "long": "",
            "logo": "/public/_45a5645a-856c-4e6e-8bbc-4c0d6955ebc3.jpeg",
            "cat": "Contenu / Vidéo",
            "tags": "#tiktok #youtube #scripts",
        },
        {
            "name": "DesignPrompt Pro",
            "url": base_url + "?from=annuaire&tool=designprompt",
            "short": "Prompts prêts à l’emploi pour créer des visuels cohérents avec votre marque.",
            "long": "",
            "logo": "/public/_9071e625-9240-4f70-a2b4-1bce79ba1a08.jpeg",
            "cat": "Design / Création",
            "tags": "#design #image #prompt",
        },
        {
            "name": "CodeBuddy Autocomplete",
            "url": base_url + "?from=annuaire&tool=codebuddy",
            "short": "Complétion de code IA pour accélérer le développement.",
            "long": "",
            "logo": "/public/_a6447d4d-91cd-4489-9ad7-051b253af9c2.jpeg",
            "cat": "Développement",
            "tags": "#dev #autocomplete",
        },
        {
            "name": "DataSense Analytics",
            "url": base_url + "?from=annuaire&tool=datasense",
            "short": "Analyse vos ventes et détecte les signaux faibles.",
            "long": "",
            "logo": "/public/_da639825-757a-4063-b28c-943ab8fbb39a.jpeg",
            "cat": "Analytics",
            "tags": "#data #analytics",
        },
        {
            "name": "MeetingNotes AI",
            "url": base_url + "?from=annuaire&tool=meetingnotes",
            "short": "Transcrit vos réunions et envoie un compte rendu structuré.",
            "long": "",
            "logo": "/public/_bdfc08c2-1c00-4300-ba77-694125dce085.jpeg",
            "cat": "Productivité",
            "tags": "#meetings #notes",
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
            (
                t["name"],
                t["url"],
                t["short"],
                t["long"],
                t["logo"],
                t["cat"],
                t["tags"],
                now,
            ),
        )


def init_db() -> None:
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
        row = db.execute("SELECT COUNT(*) AS c FROM tools").fetchone()
        if row["c"] == 0:
            seed_tools(db)


# ============================================================
# ROUTES PRINCIPALES
# ============================================================

@app.route("/")
def index():
    with get_db() as db:
        tools = db.execute(
            """
            SELECT id, name, url, short_description, logo_url, category, tags
            FROM tools
            WHERE is_published = 1
            ORDER BY
                CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                created_at DESC
            LIMIT 6;
            """
        ).fetchall()

    return render_template("index.html", tools=tools)


@app.route("/annuaire")
def annuaire_list():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        if q:
            pattern = f"%{q}%"
            tools = db.execute(
                """
                SELECT id, name, url, short_description, logo_url, category, tags
                FROM tools
                WHERE is_published = 1
                  AND (
                    name LIKE ?
                    OR url LIKE ?
                    OR short_description LIKE ?
                    OR long_description LIKE ?
                    OR category LIKE ?
                    OR tags LIKE ?
                  )
                ORDER BY
                    CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                    created_at DESC;
                """,
                (pattern, pattern, pattern, pattern, pattern, pattern),
            ).fetchall()
        else:
            tools = db.execute(
                """
                SELECT id, name, url, short_description, logo_url, category, tags
                FROM tools
                WHERE is_published = 1
                ORDER BY
                    CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                    created_at DESC;
                """
            ).fetchall()

    return render_template("annuaire_list.html", tools=tools, query=q)


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


# ============================================================
# AJOUT + STRIPE
# ============================================================

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
                short_desc,
                long_desc,
                logo_url,
                category,
                tags,
                created_at,
            ),
        )
        tool_id = cur.lastrowid

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
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

    return redirect(session.url, code=303)


# alias /ajouter/ au cas où un template l’utilise
@app.route("/ajouter/", methods=["GET", "POST"])
def ajouter():
    return ajouter_tool()


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
            db.execute(
                "DELETE FROM tools WHERE id = ? AND is_published = 0",
                (tool_id,),
            )
    return "Paiement annulé."


# ============================================================
# GOOGLE SEARCH CONSOLE
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
        tools = db.execute(
            """
            SELECT id, created_at, name
            FROM tools
            WHERE is_published = 1
            ORDER BY
                CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                created_at DESC;
            """
        ).fetchall()

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for u in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{u['loc']}</loc>")
        xml.append(f"    <priority>{u['priority']}</priority>")
        xml.append("  </url>")

    for t in tools:
        xml.append("  <url>")
        xml.append(f"    <loc>{base}/tool/{t['id']}</loc>")
        xml.append(f"    <lastmod>{t['created_at']}</lastmod>")
        xml.append("    <priority>0.8</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")


# ============================================================
# SERVE /public FILES
# ============================================================

@app.route("/public/<path:filename>")
def public_files(filename: str):
    return send_from_directory("public", filename)


# ============================================================
# INIT DB
# ============================================================

with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
