# Annuaire des créateurs d'IA – Spectra Media AI

Projet Flask minimal prêt à l'emploi pour lister des outils / agents IA avec un listing payant (Stripe) ou un mode démo.

## Lancement rapide (local)

```bash
cd annuaire_ai
python3 -m venv venv
source venv/bin/activate  # sous macOS / Linux

pip install -r requirements.txt

# Optionnel : copier .env.example vers .env et ajouter tes clés Stripe
cp .env.example .env

# Lancement
export FLASK_APP=app.py
flask run
```

En mode démo (sans Stripe configuré), l'ajout d'un outil crée directement la fiche sans paiement.

Pour activer le mode payant :
- Crée un prix unique 20€ dans Stripe et copie son `price_xxx` dans `STRIPE_PRICE_ID`
- Ajoute tes clés `STRIPE_SECRET_KEY` et `STRIPE_PUBLIC_KEY` dans `.env`
