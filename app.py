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


def seed_tools(db: sqlite3.Connection) -> None:
    """Ajoute des outils IA crédibles s'il n'y en a aucun (avec logos)."""
    now = datetime.utcnow().isoformat()

    seeds = [
        {
            "name": "Betty Bots — Assistante IA métier",
            "url": "https://www.spectramedia.online/",
            "short": "Flotte d’assistantes IA spécialisées par métier qui qualifient vos leads automatiquement.",
            "long": (
                "Betty Bots est une flotte d’assistantes IA spécialisées par métier "
                "(artisan, restauration, esthétique, médical, immobilier…). "
                "Chaque Betty répond comme une vraie assistante humaine, pose les bonnes questions, "
                "qualifie les prospects et envoie des emails prêts à traiter."
            ),
            "logo": "https://via.placeholder.com/64/FF3366/FFFFFF?text=BB",
            "cat": "Assistant IA / Lead gen",
            "tags": "#leads #PME #assistantIA",
        },
        {
            "name": "SalesPilot AI",
            "url": "https://example.com/salespilot",
            "short": "Relances commerciales automatiques et scoring de prospects.",
            "long": "",
            "logo": "https://via.placeholder.com/64/1E90FF/FFFFFF?text=SP",
            "cat": "Sales Automation",
            "tags": "#sales #crm #automation",
        },
        {
            "name": "DocuSense IA",
            "url": "https://example.com/docusense",
            "short": "Posez des questions à vos PDF, contrats et procédures internes.",
            "long": "",
            "logo": "https://via.placeholder.com/64/32CD32/FFFFFF?text=DS",
            "cat": "Knowledge Base",
            "tags": "#documentation #pdf #qa",
        },
        {
            "name": "SupportGenie AI",
            "url": "https://example.com/supportgenie",
            "short": "Chat de support client IA disponible 24/7.",
            "long": "",
            "logo": "https://via.placeholder.com/64/FFD700/000000?text=SG",
            "cat": "Support Client",
            "tags": "#support #saas #helpdesk",
        },
        {
            "name": "VideoScript Studio",
            "url": "https://example.com/videoscript",
            "short": "Génère des scripts pour TikTok, Reels et YouTube en quelques secondes.",
            "long": "",
            "logo": "https://via.placeholder.com/64/8A2BE2/FFFFFF?text=VS",
            "cat": "Contenu / Vidéo",
            "tags": "#tiktok #youtube #scripts",
        },
        {
            "name": "DesignPrompt Pro",
            "url": "https://example.com/designprompt",
            "short": "Prompts prêts à l’emploi pour créer des visuels cohérents avec votre marque.",
            "long": "",
            "logo": "https://via.placeholder.com/64/FF8C00/FFFFFF?text=DP",
            "cat": "Design / Création",
            "tags": "#design #image #prompt",
        },
        {
            "name": "CodeBuddy Autocomplete",
            "url": "https://example.com/codebuddy",
            "short": "Complétion de code IA pour accélérer le développement.",
            "long": "",
            "logo": "https://via.placeholder.com/64/00CED1/FFFFFF?text=CB",
            "cat": "Développement",
            "tags": "#dev #autocomplete",
        },
        {
            "name": "HRMatch IA",
            "url": "https://example.com/hrmatch",
            "short": "Filtre les CV et propose une short-list de candidats.",
            "long": "",
            "logo": "https://via.placeholder.com/64/DC143C/FFFFFF?text=HR",
            "cat": "RH / Recrutement",
            "tags": "#rh #recrutement #cv",
        },
        {
            "name": "LegalDraft AI",
            "url": "https://example.com/legaldraft",
            "short": "Assistance à la rédaction de contrats et courriers juridiques.",
            "long": "",
            "logo": "https://via.placeholder.com/64/2F4F4F/FFFFFF?text=LD",
            "cat": "Légal",
            "tags": "#legal #contrats",
        },
        {
            "name": "EmailFlow Optimizer",
            "url": "https://example.com/emailflow",
            "short": "Optimisation IA de vos séquences d’emails marketing.",
            "long": "",
            "logo": "https://via.placeholder.com/64/FF1493/FFFFFF?text=EF",
            "cat": "Emailing",
            "tags": "#email #marketing",
        },
        {
            "name": "SocialBoost AI",
            "url": "https://example.com/socialboost",
            "short": "Propose des posts adaptés à chaque réseau social.",
            "long": "",
            "logo": "https://via.placeholder.com/64/7FFF00/000000?text=SB",
            "cat": "Social Media",
            "tags": "#socialmedia #content",
        },
        {
            "name": "DataSense Analytics",
            "url": "https://example.com/datasense",
            "short": "Analyse vos ventes et détecte les signaux faibles.",
            "long": "",
            "logo": "https://via.placeholder.com/64/00BFFF/FFFFFF?text=DA",
            "cat": "Analytics",
            "tags": "#data #analytics",
        },
        {
            "name": "MeetingNotes AI",
            "url": "https://example.com/meetingnotes",
            "short": "Transcrit vos réunions et envoie un compte rendu structuré.",
            "long": "",
            "logo": "https://via.placeholder.com/64/FF4500/FFFFFF?text=MN",
            "cat": "Productivité",
            "tags": "#meetings #notes",
        },
        {
            "name": "VoiceAssist Studio",
            "url": "https://example.com/voiceassist",
            "short": "Crée des assistants vocaux IA pour hotline et standard téléphonique.",
            "long": "",
            "logo": "https://via.placeholder.com/64/4B0082/FFFFFF?text=VA",
            "cat": "Voix / Téléphonie",
            "tags": "#voice #ivr",
        },
        {
            "name": "EcomPricing IA",
            "url": "https://example.com/ecompricing",
            "short": "Optimise automatiquement les prix de votre boutique en ligne.",
            "long": "",
            "logo": "https://via.placeholder.com/64/228B22/FFFFFF?text=EP",
            "cat": "E-commerce",
            "tags": "#ecommerce #pricing",
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
# ROUTES PRINCIPALES (HOME + ANNUIRE + FICHE)
# ============================================================

@app.route("/")
def index():
    """Home : présentation + derniers outils (Betty toujours en tête)."""
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
    """
    Liste complète + recherche.
    ?q=term → filtre sur nom / catégorie / tags / descriptions.
    Betty Bots reste toujours en premier.
    """
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
# GOOGLE SEARCH CONSOLE (FICHIER HTML)
# ============================================================

@app.route("/google8334646a4a411e97.html")
def google_verification():
    # Doit correspondre EXACTEMENT au fichier donné par Google
    return "google-site-verification: google8334646a4a411e97.html"


# ============================================================
# ROBOTS.TXT + SITEMAP (SEO)
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
            SELECT id, created_at
            FROM tools
            WHERE is_published = 1
            ORDER BY
                CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                created_at DESC;
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
        if "lastmod" in u:
            xml.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml.append(f"    <priority>{u['priority']}</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")


# ============================================================
# INIT DB AU DÉMARRAGE
# ============================================================

with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
