# FixJeICT v2

Een modern ticketsysteem gebouwd met FastAPI voor IT-support.

## Installatie

Voer het volgende commando uit op je server:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ivoozz/fixjeictv2/main/install.sh)
```

## Kenmerken

- **FastAPI** - Snel en modern Python framework
- **Magic Links** - Veilig inloggen zonder wachtwoord
- **Basic Auth** - Beveiligde admin omgeving
- **SQLite Database** - Geen aparte database server nodig
- **Cloudflare Ready** - ProxyHeaders middleware ingebouwd

## Structuur

```
/app/
  main.py          - Hoofd FastAPI applicatie
  config.py        - Pydantic Settings
  database.py      - SQLAlchemy setup
  models.py        - Database modellen
  auth.py          - Authenticatie
  templates/       - Jinja2 templates
  static/          - CSS, JS, afbeeldingen
  routers/
    public.py      - Publieke routes
    admin.py       - Admin routes
```

## Services

- **Public**: Draait op poort 5000 - Voor klanten
- **Admin**: Draait op poort 5001 - Voor beheerders (Basic Auth)

## Beheer

```bash
# Logs bekijken
journalctl -u fixjeict-public -f
journalctl -u fixjeict-admin -f

# Services herstarten
systemctl restart fixjeict-public
systemctl restart fixjeict-admin

# Status check
systemctl status fixjeict-public
systemctl status fixjeict-admin
```

## Cloudflare Tunnel

Voor Cloudflare tunnel configuratie:

```yaml
# public tunnel
tunnel: <your-tunnel-id>
ingress:
  - hostname: fixjeict.nl
    service: http://10.10.10.13:5000
  - service: http_status:404

# admin tunnel
tunnel: <your-tunnel-id>
ingress:
  - hostname: admin.fixjeict.nl
    service: http://10.10.10.13:5001
  - service: http_status:404
```

## Ontwikkeling

```bash
# Clone repository
git clone https://github.com/Ivoozz/fixjeictv2.git
cd fixjeictv2

# Virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Bewerk .env met je instellingen

# Database initialiseren
cd app
python -c "from database import init_db; init_db()"

# Development server starten
uvicorn main:public_app --reload --port 5000
uvicorn main:admin_app --reload --port 5001
```

## Licentie

MIT License
