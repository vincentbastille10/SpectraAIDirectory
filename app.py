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
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

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


def slugify(name: str) -> str:
    """
    Transforme un nom d'outil en slug URL-safe très simple.
    Exemple : "Betty Bots — Assistante IA" -> "betty-bots-assistante-ia"
    """
    s = name.lower()
    s = "".join(ch if ch.isalnum() else "-" for ch in s)
    while "--" in s:
        s = s.replace("--", "-")
    s = s.strip("-")
    if not s:
        s = "tool"
    return s


def generate_unique_slug(db: sqlite3.Connection, name: str) -> str:
    """
    Génère un slug unique sur la table tools.
    """
    base = slugify(name)
    slug = base
    suffix = 2
    while True:
        row = db.execute(
            "SELECT 1 FROM tools WHERE slug = ? LIMIT 1",
            (slug,),
        ).fetchone()
        if row is None:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def seed_tools(db: sqlite3.Connection) -> None:
    """
    Seed initial d'outils IA :
    - Betty Bots en tête
    - Puis des outils IA réels connus (ChatGPT, Sora, etc.)
    """
    now = datetime.utcnow().isoformat()
    base_url = "https://www.spectramedia.online/"

    seeds = [
        # ==============================
        # 1. BETTY BOTS EN TÊTE
        # ==============================
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

        # ==============================
        # 2. OUTILS IA GÉNÉRALISTES
        # ==============================
        {
            "name": "ChatGPT (OpenAI)",
            "url": "https://chat.openai.com/",
            "short": "Assistant IA généraliste pour rédiger, coder, analyser et brainstormer.",
            "long": "ChatGPT est un assistant conversationnel IA polyvalent qui aide à rédiger, résumer, coder, traduire et explorer des idées.",
            "logo": "",
            "cat": "Assistant IA généraliste",
            "tags": "#chatgpt #assistant #openai",
        },
        {
            "name": "Claude 3.5 Sonnet",
            "url": "https://claude.ai/",
            "short": "Assistant IA avancé pour l’écriture, l’analyse et le travail en profondeur.",
            "long": "Claude est un modèle d’IA développé par Anthropic, conçu pour la réflexion, la rédaction structurée et l’analyse de documents.",
            "logo": "",
            "cat": "Assistant IA généraliste",
            "tags": "#claude #anthropic #assistant",
        },
        {
            "name": "Perplexity AI",
            "url": "https://www.perplexity.ai/",
            "short": "Moteur de recherche IA avec réponses sourcées et conversationnelles.",
            "long": "Perplexity combine moteur de recherche et IA générative pour proposer des réponses sourcées, interactives et à jour.",
            "logo": "",
            "cat": "Recherche IA",
            "tags": "#search #perplexity #qa",
        },
        {
            "name": "Gemini (Google AI)",
            "url": "https://gemini.google.com/",
            "short": "Assistant IA de Google pour recherche, écriture et productivité.",
            "long": "Gemini est l’assistant IA de Google, intégré à l’écosystème Google pour la recherche, l’écriture et la productivité.",
            "logo": "",
            "cat": "Assistant IA généraliste",
            "tags": "#gemini #google #assistant",
        },

        # ==============================
        # 3. IA IMAGES & VIDÉO
        # ==============================
        {
            "name": "Midjourney",
            "url": "https://www.midjourney.com/",
            "short": "Générateur d’images IA à partir de prompts textuels.",
            "long": "Midjourney permet de créer des visuels détaillés et artistiques à partir de simples descriptions textuelles.",
            "logo": "",
            "cat": "Image / Génération visuelle",
            "tags": "#midjourney #image #generation",
        },
        {
            "name": "Sora (OpenAI Video)",
            "url": "https://openai.com/sora",
            "short": "Génération de vidéos à partir de texte (accès restreint).",
            "long": "Sora est un modèle de génération vidéo développé par OpenAI, capable de produire des séquences à partir de descriptions textuelles.",
            "logo": "",
            "cat": "Vidéo / Génération",
            "tags": "#sora #video #openai",
        },
        {
            "name": "Runway Gen-3 Alpha",
            "url": "https://runwayml.com/",
            "short": "Suite créative IA pour génération et montage vidéo.",
            "long": "Runway propose des outils pour générer, éditer et styliser des vidéos avec l’aide de l’intelligence artificielle.",
            "logo": "",
            "cat": "Vidéo / Création",
            "tags": "#runway #video #creation",
        },
        {
            "name": "Pika Labs",
            "url": "https://www.pika.art/",
            "short": "Outil de génération vidéo à partir de texte ou d’images.",
            "long": "Pika permet de générer des vidéos courtes et stylisées à partir de prompts textuels ou d’images sources.",
            "logo": "",
            "cat": "Vidéo / Génération",
            "tags": "#pika #video #ai",
        },
        {
            "name": "Leonardo AI",
            "url": "https://leonardo.ai/",
            "short": "Plateforme IA pour créer des images, textures et assets de jeu.",
            "long": "Leonardo AI est spécialisée dans la création de visuels, textures et assets pour les jeux vidéo et le design.",
            "logo": "",
            "cat": "Image / Création",
            "tags": "#leonardo #image #assets",
        },
        {
            "name": "Ideogram AI",
            "url": "https://ideogram.ai/",
            "short": "Générateur d’images IA avec texte intégré propre.",
            "long": "Ideogram permet de créer des visuels avec du texte lisible, idéal pour affiches, posts réseaux sociaux et visuels marketing.",
            "logo": "",
            "cat": "Image / Design",
            "tags": "#ideogram #image #text",
        },

        # ==============================
        # 4. IA AUDIO & VOIX
        # ==============================
        {
            "name": "ElevenLabs",
            "url": "https://elevenlabs.io/",
            "short": "Synthèse vocale IA réaliste dans de nombreuses langues.",
            "long": "ElevenLabs permet de générer des voix naturelles, cloner des voix existantes et propose des API pour la narration et le doublage.",
            "logo": "",
            "cat": "Audio / Voix",
            "tags": "#voice #elevenlabs #audio",
        },
        {
            "name": "Descript",
            "url": "https://www.descript.com/",
            "short": "Montage audio/vidéo par édition de texte.",
            "long": "Descript propose un montage audio et vidéo piloté par texte, avec transcription, overdub et édition intuitive.",
            "logo": "",
            "cat": "Audio / Vidéo",
            "tags": "#descript #podcast #video",
        },
        {
            "name": "Krisp AI",
            "url": "https://krisp.ai/",
            "short": "Suppression du bruit en temps réel pour appels et réunions.",
            "long": "Krisp utilise l’IA pour filtrer les bruits de fond lors des appels, réunions et enregistrements.",
            "logo": "",
            "cat": "Audio / Productivité",
            "tags": "#noise #krisp #calls",
        },
        {
            "name": "Otter.ai",
            "url": "https://otter.ai/",
            "short": "Transcription automatique de réunions et conférences.",
            "long": "Otter transcrit les réunions en temps réel, fournit des résumés et permet de rechercher dans les comptes rendus.",
            "logo": "",
            "cat": "Transcription",
            "tags": "#otter #transcription #meetings",
        },

        # ==============================
        # 5. IA POUR DÉVELOPPEURS
        # ==============================
        {
            "name": "GitHub Copilot",
            "url": "https://github.com/features/copilot",
            "short": "Assistant de complétion de code intégré à l’IDE.",
            "long": "GitHub Copilot aide les développeurs à écrire du code plus vite grâce à des suggestions contextuelles basées sur l’IA.",
            "logo": "",
            "cat": "Développement",
            "tags": "#copilot #dev #code",
        },
        {
            "name": "Cursor IDE",
            "url": "https://www.cursor.com/",
            "short": "IDE augmentée par l’IA pour coder plus vite.",
            "long": "Cursor est un environnement de développement intégré qui place l’IA au cœur du workflow de programmation.",
            "logo": "",
            "cat": "Développement",
            "tags": "#cursor #ide #ai",
        },
        {
            "name": "Codeium",
            "url": "https://www.codeium.com/",
            "short": "Complétion de code IA gratuite pour de nombreux langages.",
            "long": "Codeium propose une complétion IA et des assistants de refactorisation pour de nombreux langages.",
            "logo": "",
            "cat": "Développement",
            "tags": "#codeium #autocomplete #dev",
        },
        {
            "name": "Tabnine",
            "url": "https://www.tabnine.com/",
            "short": "Assistant de complétion IA pour développeurs.",
            "long": "Tabnine fournit de la complétion de code contextuelle pour les équipes et les projets privés.",
            "logo": "",
            "cat": "Développement",
            "tags": "#tabnine #code #assistant",
        },
        {
            "name": "Replicate",
            "url": "https://replicate.com/",
            "short": "Hébergement de modèles IA via API (image, texte, audio…).",
            "long": "Replicate permet d’exécuter des modèles IA via API sans gérer l’infrastructure, pour l’image, la vidéo, le texte ou l’audio.",
            "logo": "",
            "cat": "Infrastructure IA",
            "tags": "#replicate #api #models",
        },
        {
            "name": "Banana.dev",
            "url": "https://www.banana.dev/",
            "short": "Déploiement de modèles IA sur GPU via API.",
            "long": "Banana.dev propose un hébergement simple de modèles IA sur GPU avec facturation à l’usage.",
            "logo": "",
            "cat": "Infrastructure IA",
            "tags": "#banana #gpu #hosting",
        },
        {
            "name": "Hugging Face",
            "url": "https://huggingface.co/",
            "short": "Plateforme de modèles IA open source et hub de datasets.",
            "long": "Hugging Face regroupe des milliers de modèles et datasets IA open source, avec des espaces déployables en un clic.",
            "logo": "",
            "cat": "Modèles IA / Open Source",
            "tags": "#huggingface #models #opensource",
        },

        # ==============================
        # 6. IA MARKETING & CONTENU
        # ==============================
        {
            "name": "Jasper AI",
            "url": "https://www.jasper.ai/",
            "short": "Assistant IA pour la rédaction marketing et les pages de vente.",
            "long": "Jasper aide à rédiger des textes marketing, emails, landing pages et posts réseaux sociaux en quelques minutes.",
            "logo": "",
            "cat": "Marketing / Rédaction",
            "tags": "#jasper #copywriting #marketing",
        },
        {
            "name": "Copy.ai",
            "url": "https://www.copy.ai/",
            "short": "Plateforme de génération de textes marketing et emails.",
            "long": "Copy.ai propose des modèles pour rédiger rapidement des emails, publicités, scripts vidéo et contenus social media.",
            "logo": "",
            "cat": "Marketing / Rédaction",
            "tags": "#copyai #marketing #content",
        },
        {
            "name": "Writesonic",
            "url": "https://writesonic.com/",
            "short": "Outil IA pour blogs, landing pages et publicités.",
            "long": "Writesonic génère des articles, des pages de vente et des annonces à partir de quelques indications.",
            "logo": "",
            "cat": "Marketing / Rédaction",
            "tags": "#writesonic #blog #ads",
        },
        {
            "name": "Tome",
            "url": "https://tome.app/",
            "short": "Création de présentations et de récits visuels avec l’IA.",
            "long": "Tome utilise l’IA pour générer des présentations, supports visuels et récits interactifs à partir de prompts.",
            "logo": "",
            "cat": "Présentation / Storytelling",
            "tags": "#tome #presentation #story",
        },
        {
            "name": "Synthesia",
            "url": "https://www.synthesia.io/",
            "short": "Création de vidéos avec avatars IA à partir de texte.",
            "long": "Synthesia permet de créer des vidéos avec avatars IA qui lisent un script, idéal pour la formation et le marketing.",
            "logo": "",
            "cat": "Vidéo / Avatar",
            "tags": "#synthesia #avatar #video",
        },
        {
            "name": "HeyGen",
            "url": "https://www.heygen.com/",
            "short": "Génération de vidéos avec avatars IA personnalisables.",
            "long": "HeyGen propose des avatars IA et du lip-sync pour créer des vidéos personnalisées à partir de texte.",
            "logo": "",
            "cat": "Vidéo / Avatar",
            "tags": "#heygen #avatar #ai",
        },

        # ==============================
        # 7. IA PRODUCTIVITÉ & BUREAU
        # ==============================
        {
            "name": "Notion AI",
            "url": "https://www.notion.so/product/ai",
            "short": "IA intégrée à Notion pour résumer, écrire et organiser.",
            "long": "Notion AI aide à résumer des notes, générer du contenu et réorganiser l’information dans Notion.",
            "logo": "",
            "cat": "Productivité",
            "tags": "#notion #notes #productivity",
        },
        {
            "name": "ClickUp AI",
            "url": "https://clickup.com/",
            "short": "Assistant IA intégré pour la gestion de projet.",
            "long": "ClickUp AI propose rédaction, résumés et aide à la gestion de tâches au sein de la plateforme ClickUp.",
            "logo": "",
            "cat": "Gestion de projet",
            "tags": "#clickup #project #ai",
        },
        {
            "name": "Motion AI",
            "url": "https://www.usemotion.com/",
            "short": "Planification automatique de tâches et réunions avec IA.",
            "long": "Motion IA planifie automatiquement votre agenda et vos tâches pour optimiser votre temps.",
            "logo": "",
            "cat": "Planification / Agenda",
            "tags": "#motion #agenda #automation",
        },
        {
            "name": "Fireflies.ai",
            "url": "https://fireflies.ai/",
            "short": "Assistant IA pour prise de notes en réunion.",
            "long": "Fireflies enregistre et transcrit les réunions, puis extrait des tâches et décisions clés.",
            "logo": "",
            "cat": "Réunions / Transcription",
            "tags": "#fireflies #meetings #notes",
        },

        # ==============================
        # 8. AUTOMATION & NO-CODE
        # ==============================
        {
            "name": "Zapier",
            "url": "https://zapier.com/",
            "short": "Automatisation de workflows entre apps, avec des fonctions IA.",
            "long": "Zapier connecte des milliers d’applications et permet d’automatiser des workflows, avec des blocs IA intégrés.",
            "logo": "",
            "cat": "Automation / No-code",
            "tags": "#zapier #automation #nocode",
        },
        {
            "name": "Make (ex-Integromat)",
            "url": "https://www.make.com/",
            "short": "Plateforme d’automatisation visuelle avec intégrations IA.",
            "long": "Make permet de construire des scénarios d’automatisation complexes, incluant des appels à des API IA.",
            "logo": "",
            "cat": "Automation / No-code",
            "tags": "#make #automation #nocode",
        },
        {
            "name": "n8n",
            "url": "https://n8n.io/",
            "short": "Outil d’automatisation open source extensible.",
            "long": "n8n est une alternative open source à Zapier/Make pour créer des workflows automatisés, y compris autour de l’IA.",
            "logo": "",
            "cat": "Automation / Open Source",
            "tags": "#n8n #automation #opensource",
        },

        # ==============================
        # 9. IA ORIENTÉ BUSINESS / PME
        # ==============================
        {
            "name": "Durable.co",
            "url": "https://durable.co/",
            "short": "Création de sites web pour petites entreprises avec IA.",
            "long": "Durable génère un site web pour une petite entreprise en quelques minutes à partir de quelques questions.",
            "logo": "",
            "cat": "Site web / PME",
            "tags": "#durable #website #smallbusiness",
        },
        {
            "name": "Mixo.io",
            "url": "https://mixo.io/",
            "short": "Création de landing pages pour tester des idées.",
            "long": "Mixo aide à créer rapidement une landing page pour valider une idée ou un produit avec l’aide de l’IA.",
            "logo": "",
            "cat": "Landing pages",
            "tags": "#mixo #landingpage #startup",
        },
        {
            "name": "Tidio AI",
            "url": "https://www.tidio.com/",
            "short": "Chatbot IA pour sites e-commerce et support client.",
            "long": "Tidio combine chat en direct et chatbot IA pour répondre aux clients sur les sites e-commerce.",
            "logo": "",
            "cat": "Chatbot / Support",
            "tags": "#tidio #chatbot #ecommerce",
        },
        {
            "name": "HubSpot AI",
            "url": "https://www.hubspot.com/",
            "short": "Fonctions IA intégrées au CRM HubSpot.",
            "long": "HubSpot ajoute des fonctionnalités IA pour la rédaction d’emails, la segmentation et la priorisation des leads.",
            "logo": "",
            "cat": "CRM / Marketing",
            "tags": "#hubspot #crm #ai",
        },
    ]

    for t in seeds:
        slug = generate_unique_slug(db, t["name"])
        db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, slug, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                t["name"],
                t["url"],
                t["short"],
                t["long"],
                t["logo"],
                t["cat"],
                t["tags"],
                slug,
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
                slug TEXT,
                created_at TEXT NOT NULL,
                is_published INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        # Migration légère : s'assurer que la colonne slug existe
        cols = db.execute("PRAGMA table_info(tools);").fetchall()
        col_names = [c["name"] for c in cols]
        if "slug" not in col_names:
            db.execute("ALTER TABLE tools ADD COLUMN slug TEXT;")

        # Remplir les slugs manquants si nécessaire
        rows = db.execute(
            "SELECT id, name FROM tools WHERE slug IS NULL OR slug = '';"
        ).fetchall()
        for r in rows:
            slug = generate_unique_slug(db, r["name"])
            db.execute("UPDATE tools SET slug = ? WHERE id = ?;", (slug, r["id"]))

        row = db.execute("SELECT COUNT(*) AS c FROM tools;").fetchone()
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
            SELECT id, name, url, short_description, logo_url, category, tags, slug
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
                SELECT id, name, url, short_description, logo_url, category, tags, slug
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
                SELECT id, name, url, short_description, logo_url, category, tags, slug
                FROM tools
                WHERE is_published = 1
                ORDER BY
                    CASE WHEN name LIKE 'Betty Bots%' THEN 0 ELSE 1 END,
                    created_at DESC;
                """
            ).fetchall()

    return render_template("annuaire_list.html", tools=tools, query=q)


@app.route("/tool/<slug>")
def tool_detail(slug: str):
    with get_db() as db:
        tool = db.execute(
            """
            SELECT *
            FROM tools
            WHERE slug = ? AND is_published = 1;
            """,
            (slug,),
        ).fetchone()

    if not tool:
        abort(404)

    return render_template("tool_detail.html", tool=tool)


# ============================================================
# AJOUT + STRIPE (FORMULAIRE + CHECKOUT)
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

    # On insère l'outil en brouillon (is_published = 0) avec slug unique
    with get_db() as db:
        slug = generate_unique_slug(db, name)
        cur = db.execute(
            """
            INSERT INTO tools (
                name, url, short_description, long_description,
                logo_url, category, tags, slug, created_at, is_published
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                name,
                url_site,
                short_desc,
                long_desc,
                logo_url,
                category,
                tags,
                slug,
                created_at,
            ),
        )
        tool_id = cur.lastrowid

    try:
        # Checkout Stripe avec metadata pour le webhook
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
            metadata={
                "tool_id": str(tool_id),
                "name": name,
                "url": url_site,
                "short_description": short_desc,
                "long_description": long_desc,
                "logo_url": logo_url,
                "category": category,
                "tags": tags,
            },
        )
    except Exception as e:
        # En cas d'erreur Stripe, on supprime le brouillon
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
    """
    Route appelée par Stripe après paiement réussi.
    Sécurise la publication (en plus du webhook).
    """
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
# STRIPE WEBHOOK (OPTIONNEL MAIS CONSEILLÉ)
# ============================================================

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    Webhook Stripe :
    - Écoute checkout.session.completed
    - Publie l’outil (is_published = 1) même si l’utilisateur
      ne revient pas sur la page de succès.
    """
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        else:
            # Sans secret, on parse basiquement le JSON
            event = request.get_json(force=True)
    except Exception as e:
        return str(e), 400

    event_type = event["type"] if isinstance(event, dict) else event.type
    data_object = event["data"]["object"] if isinstance(event, dict) else event.data.object

    if event_type == "checkout.session.completed":
        metadata = getattr(data_object, "metadata", None) or data_object.get("metadata", {})
        tool_id = metadata.get("tool_id")

        if tool_id:
            with get_db() as db:
                db.execute(
                    "UPDATE tools SET is_published = 1 WHERE id = ?",
                    (tool_id,),
                )

    return "ok", 200


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
            SELECT slug, created_at, name
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
        xml.append(f"    <loc>{base}/tool/{t['slug']}</loc>")
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
