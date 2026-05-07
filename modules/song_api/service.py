import requests
from modules.song_api.config import load_config, save_config


class SongAPIService:

    # =========================
    # SETTINGS
    # =========================

    def get_settings(self):
        return load_config()

    def update_settings(self, data: dict):
        cfg = load_config()

        # 🔥 обновляем ВСЕ нужные поля
        if "api_url" in data:
            cfg["api_url"] = (data.get("api_url") or "").strip()

        if "model" in data:
            cfg["model"] = (data.get("model") or "").strip()

        if "lm_model" in data:
            cfg["lm_model"] = data.get("lm_model") or None

        save_config(cfg)

        print(
            f"[SongAPI] ⚙️ updated: api={cfg.get('api_url')} | "
            f"model={cfg.get('model')} | lm={cfg.get('lm_model')}"
        )

    # =========================
    # MODELS INVENTORY
    # =========================

    def get_models_inventory(self):
        cfg = load_config()
        api = "http://192.168.1.18:8001"

        if not api:
            return {"models": [], "lm_models": [], "error": "no_api"}

        try:
            r = requests.get(f"{api}/v1/model_inventory", timeout=10)

            if r.status_code != 200:
                return {"models": [], "lm_models": [], "error": "http_error"}

            data = r.json()

            if data.get("code") != 200:
                return {"models": [], "lm_models": [], "error": "api_error"}

            payload = data.get("data", {})

            return {
                "models": payload.get("models", []),
                "lm_models": payload.get("lm_models", [])
            }

        except Exception as e:
            return {"models": [], "lm_models": [], "error": str(e)}

    # =========================
    # INIT MODEL
    # =========================

    def init_model(self):
        cfg = load_config()
        api = "http://192.168.1.18:8001"

        if not api:
            print("[SongAPI] ❌ API URL not set")
            return

        model = cfg.get("model")
        lm_model = cfg.get("lm_model")

        if not model:
            print("[SongAPI] ❌ model not set")
            return

        try:
            print(f"[SongAPI] ⚙️ init model: {model}")

            payload = {
                "model": model,
                "init_llm": bool(lm_model)
            }

            if lm_model:
                payload["lm_model_path"] = lm_model

            r = requests.post(
                f"{api}/v1/init",
                json=payload,
                timeout=30
            )

            if r.status_code != 200:
                print("[SongAPI] ❌ init failed:", r.text)
                return

            print(f"[SongAPI] ✅ model ready: {model} | LM: {lm_model}")

        except Exception as e:
            print("[SongAPI] ❌ init error:", e)


# =========================
# SINGLETON
# =========================

song_api_service = SongAPIService()