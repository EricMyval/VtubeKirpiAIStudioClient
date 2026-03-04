# modules/donation/donation_parser.py
import json
import threading
import time
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from modules.donate_admin.repository import DonateRepository
import requests
from modules.utils.currency_converter import CurrencyConverter

# где храним настройки OAuth (вводятся из вебки)
DONATIONALERTS_CFG_FILE = Path("data/db/donationalerts_oauth.json")

# где храним токен (как ты просил)
TOKEN_FILE = Path("data/db/donation_token.json")

TOKEN_URL = "https://www.donationalerts.com/oauth/token"
DONATION_API_URL = "https://www.donationalerts.com/api/v1/alerts/donations"
SCOPE = "oauth-donation-index"


# ------------------ CONFIG ------------------

def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def load_da_cfg() -> dict:
    """
    return:
      {
        "client_id": "...",
        "client_secret": "...",
        "redirect_uri": "http://localhost:1337/callback"
      }
    """
    try:
        with open(DONATIONALERTS_CFG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        data = {}

    # дефолты
    data.setdefault("client_id", "")
    data.setdefault("client_secret", "")
    data.setdefault("redirect_uri", "http://localhost:1337/callback")
    return data


def save_da_cfg(client_id: str, client_secret: str, redirect_uri: str):
    _ensure_parent(DONATIONALERTS_CFG_FILE)
    data = {
        "client_id": (client_id or "").strip(),
        "client_secret": (client_secret or "").strip(),
        "redirect_uri": (redirect_uri or "").strip() or "http://localhost:1337/callback",
    }
    with open(DONATIONALERTS_CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _build_oauth_url(cfg: dict) -> str:
    client_id = cfg.get("client_id", "")
    redirect_uri = cfg.get("redirect_uri", "http://localhost:1337/callback")
    return (
        "https://www.donationalerts.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        f"&scope={SCOPE}"
    )


# ------------------ AUTH SERVER ------------------

class _AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/callback" in self.path and "code=" in self.path:
            code = self.path.split("code=")[-1].split("&")[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Auth success! You can close this window.")
            self.server.code = code  # type: ignore[attr-defined]
        else:
            self.send_response(404)
            self.end_headers()

    # чтобы не спамило в консоль
    def log_message(self, format, *args):
        return


def _parse_host_port_from_redirect(redirect_uri: str) -> tuple[str, int]:
    # ожидаем http://localhost:1337/callback
    # fallback: localhost:1337
    try:
        # супер-лёгкий парсер без urllib
        # "http://localhost:1337/callback" -> "localhost:1337"
        hostport = redirect_uri.split("://", 1)[-1].split("/", 1)[0]
        host = hostport.split(":", 1)[0] or "localhost"
        port = int(hostport.split(":", 1)[1]) if ":" in hostport else 1337
        return host, port
    except Exception:
        return "localhost", 1337


def get_auth_code(cfg: dict) -> str:
    """
    Открывает браузер на OAuth URL и поднимает мини-сервер по redirect_uri.
    """
    oauth_url = _build_oauth_url(cfg)
    redirect_uri = cfg.get("redirect_uri", "http://localhost:1337/callback")
    host, port = _parse_host_port_from_redirect(redirect_uri)

    webbrowser.open(oauth_url)
    httpd = HTTPServer((host, port), _AuthHandler)
    print(f"Ожидаем авторизацию в браузере... callback: {redirect_uri}")
    httpd.handle_request()  # ждём 1 запрос
    code = getattr(httpd, "code", None)
    if not code:
        raise Exception("Не получили code из callback")
    return code


# ------------------ TOKEN LOGIC ------------------

def save_token(data: dict):
    _ensure_parent(TOKEN_FILE)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_token() -> dict | None:
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_token():
    try:
        TOKEN_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def get_token(force_reauth: bool = False) -> str:
    cfg = load_da_cfg()
    if not cfg.get("client_id") or not cfg.get("client_secret"):
        raise Exception("Donationalerts OAuth не настроен: заполни CLIENT_ID и CLIENT_SECRET в вебке.")

    if not force_reauth:
        token_data = load_token()
        if token_data and token_data.get("access_token"):
            return token_data["access_token"]

    code = get_auth_code(cfg)

    res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": cfg.get("redirect_uri", "http://localhost:1337/callback"),
            "code": code,
        },
        timeout=30,
    )

    if res.status_code == 200:
        token_data = res.json()
        save_token(token_data)
        return token_data["access_token"]

    raise Exception(f"Ошибка авторизации: {res.status_code} {res.text}")


# ------------------ MAIN LISTENER ------------------

def start_donation_listener(on_donation):
    """
    Слушает новые донаты и вызывает on_donation(name, message, amount, is_real)
    """
    try:
        access_token = get_token()
    except Exception as e:
        print(f"⚠️ DonationAlerts listener НЕ запущен: {e}")
        print("👉 Открой /donationalerts, заполни CLIENT_ID/SECRET и нажми Авторизоваться.")
        return  # <-- ключевое: НЕ падаем

    headers = {"Authorization": f"Bearer {access_token}"}
    last_known_id = None

    def loop():
        nonlocal last_known_id
        print("🎧 Запуск донат-лиснера (DonationAlerts)...")

        # Инициализация: получаем последний ID (но НЕ реагируем)
        try:
            res = requests.get(DONATION_API_URL, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                if data.get("data"):
                    last_known_id = data["data"][0]["id"]
                    print(f"🕒 Последний ID при запуске: {last_known_id}")
        except Exception as e:
            print(f"[DA init error]: {e}")

        while True:
            try:
                res = requests.get(DONATION_API_URL, headers=headers, timeout=30)

                if res.status_code == 401:
                    # токен протух/слетел — пробуем переавторизоваться 1 раз
                    print("[DA] 401 Unauthorized: пробую переавторизацию...")
                    try:
                        new_token = get_token(force_reauth=True)
                        headers["Authorization"] = f"Bearer {new_token}"
                        time.sleep(2)
                        continue
                    except Exception as e:
                        print(f"[DA reauth error]: {e}")
                        time.sleep(10)
                        continue

                if res.status_code != 200:
                    print(f"[DA request error]: {res.status_code} {res.text}")
                    time.sleep(10)
                    continue

                data = res.json()
                items = data.get("data") or []
                new_donations = []

                for d in reversed(items):  # от старых к новым
                    donation_id = d.get("id")
                    if donation_id is None:
                        continue
                    if last_known_id is None or donation_id > last_known_id:
                        new_donations.append(d)

                if new_donations:
                    for d in new_donations:
                        name = d.get("username") or "Аноним"
                        message = d.get("message") or ""
                        amount = d.get("amount") or 0

                        currency = d.get("currency") or "RUB"
                        amount_rub = CurrencyConverter.to_rub(amount, currency)

                        DonateRepository.add_donate(
                            username=name,
                            amount=amount_rub,
                            message=message,
                            extra=f"DonationAlerts:{currency}",
                        )

                        on_donation(name, message, amount, True)
                    last_known_id = new_donations[-1]["id"]

                time.sleep(5)

            except Exception as e:
                print(f"[DA listener error]: {e}")
                time.sleep(10)

    threading.Thread(target=loop, daemon=True).start()
