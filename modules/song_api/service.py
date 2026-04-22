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

        # 🔥 ВАЖНО: теперь можно перезаписывать None
        for k, v in data.items():
            cfg[k] = v

        save_config(cfg)

        print(f"[SongAPI] ⚙️ settings updated: model={cfg.get('model')} lm={cfg.get('lm_model')}")

    def is_enabled_for_amount(self, amount: float) -> bool:
        cfg = load_config()

        if not cfg.get("enabled"):
            return False

        try:
            min_amount = float(cfg.get("min_amount", 0))
        except:
            min_amount = 0.0

        try:
            max_amount = float(cfg.get("max_amount", 999999999))
        except:
            max_amount = 999999999.0

        try:
            amount = float(amount)
        except:
            return False

        return min_amount <= amount <= max_amount

    # =========================
    # MODELS INVENTORY
    # =========================

    def get_models_inventory(self):
        cfg = load_config()
        api = cfg.get("api_url")

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
        api = cfg.get("api_url")

        if not api:
            print("[SongAPI] ❌ API URL not set")
            return

        try:
            model = cfg.get("model")
            lm_model = cfg.get("lm_model")

            if not model:
                print("[SongAPI] ❌ model not set")
                return

            inventory = self.get_models_inventory()

            # =========================
            # CHECK INVENTORY
            # =========================

            if not inventory or inventory.get("error"):
                print("[SongAPI] ⚠️ inventory unavailable — forcing init")
                model_loaded = False
                lm_loaded = False
                model_exists = True
            else:
                model_loaded = False
                model_exists = False

                for m in inventory.get("models", []):
                    if m.get("name") == model:
                        model_exists = True
                        if m.get("is_loaded"):
                            model_loaded = True
                        break

                if not model_exists:
                    print(f"[SongAPI] ❌ model not found: {model}")
                    return

                lm_loaded = False

                if lm_model:
                    for lm in inventory.get("lm_models", []):
                        if lm.get("name") == lm_model and lm.get("is_loaded"):
                            lm_loaded = True
                            break

            # =========================
            # INIT MAIN MODEL
            # =========================

            if model_loaded:
                print(f"[SongAPI] ✅ model already loaded: {model}")
            else:
                print(f"[SongAPI] ⚙️ init model: {model}")

                r = requests.post(
                    f"{api}/v1/init",
                    json={
                        "model": model,
                        "init_llm": False
                    },
                    timeout=30
                )

                if r.status_code != 200:
                    print("[SongAPI] ❌ model init failed:", r.text)
                    return

                print(f"[SongAPI] ✅ model loaded: {model}")

            # =========================
            # LM LOGIC (🔥 FIXED)
            # =========================

            if lm_model:
                # ✅ включаем LM только если выбран

                if lm_loaded:
                    print(f"[SongAPI] ✅ LM already loaded: {lm_model}")
                else:
                    print(f"[SongAPI] 🧠 init LM: {lm_model}")

                    r = requests.post(
                        f"{api}/v1/init",
                        json={
                            "model": model,
                            "init_llm": True,
                            "lm_model_path": lm_model
                        },
                        timeout=30
                    )

                    if r.status_code != 200:
                        print("[SongAPI] ⚠️ LM init failed:", r.text)
                    else:
                        print(f"[SongAPI] ✅ LM loaded: {lm_model}")

            else:
                # 🔥 КЛЮЧЕВОЙ ФИКС
                print("[SongAPI] 🚫 LM disabled")

                r = requests.post(
                    f"{api}/v1/init",
                    json={
                        "model": model,
                        "init_llm": False
                    },
                    timeout=30
                )

                if r.status_code != 200:
                    print("[SongAPI] ⚠️ failed to disable LM:", r.text)

        except Exception as e:
            print("[SongAPI] ❌ init error:", e)


# =========================
# SINGLETON
# =========================

song_api_service = SongAPIService()