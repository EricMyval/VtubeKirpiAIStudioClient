# modules/donation_image/donation_image_db.py
import base64
import io
import imghdr
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional, Tuple, List, Any

import requests
from requests import RequestException
from PIL import Image


class DonationImageDB:
    """
    НОВАЯ ЛОГИКА:
    - Никаких файлов на диске.
    - Картинка хранится прямо в SQLite как base64 + mime.
    - В выдаче списка донатов наружу (web_admin) мы НЕ тащим base64,
      а возвращаем только флаг has_image (0/1).
    """

    def __init__(self, db_path: str = "data/db/donate_with_image.db"):
        self.db_path = Path(db_path)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        # чуть удобнее в отладке, но мы все равно возвращаем tuple
        # conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = self._connect()
        cur = conn.cursor()

        # 1) Базовая таблица (если ее не было)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                message TEXT NOT NULL,
                amount_user TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 2) Миграция: добавляем поля для base64 хранения (если их не было)
        existing_cols = set()
        cur.execute("PRAGMA table_info(donations)")
        for row in cur.fetchall():
            # row = (cid, name, type, notnull, dflt_value, pk)
            existing_cols.add(str(row[1]).lower())

        if "image_b64" not in existing_cols:
            cur.execute("ALTER TABLE donations ADD COLUMN image_b64 TEXT")
        if "image_mime" not in existing_cols:
            cur.execute("ALTER TABLE donations ADD COLUMN image_mime TEXT")

        conn.commit()
        conn.close()

    # ---------- image helpers ----------

    def is_valid_image_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Возвращает (ok, image_type)
        image_type: 'jpeg', 'png', 'gif', 'webp', ...
        """
        try:
            image_type = imghdr.what(None, content)
            if image_type:
                return True, image_type

            # fallback: PIL verify
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
                fmt = (img.format or "").lower() or None
                return True, fmt
            except Exception:
                return False, None
        except Exception:
            return False, None

    def _mime_from_type(self, image_type: Optional[str], content_type_header: str) -> str:
        """
        Определяем MIME, чтобы потом отдавать правильный Content-Type.
        """
        t = (image_type or "").lower().strip()
        if t in ("jpeg", "jpg", "jpe"):
            return "image/jpeg"
        if t == "png":
            return "image/png"
        if t == "gif":
            return "image/gif"
        if t == "webp":
            return "image/webp"
        if t == "bmp":
            return "image/bmp"
        if t in ("tif", "tiff"):
            return "image/tiff"

        ct = (content_type_header or "").lower()
        if "image/" in ct:
            # например image/jpeg; charset=binary
            return ct.split(";")[0].strip()

        # дефолт
        return "image/jpeg"

    def extract_direct_image_url(self, url: str) -> Optional[str]:
        """Для ibb/imgur short links: вытягиваем прямую ссылку на картинку (og:image)."""
        try:
            from bs4 import BeautifulSoup
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            meta_image = soup.find("meta", property="og:image")
            if meta_image and meta_image.get("content"):
                return meta_image["content"]

            link_image = soup.find("link", rel="image_src")
            if link_image and link_image.get("href"):
                return link_image["href"]

            for img in soup.find_all("img"):
                src = img.get("src") or ""
                if any(domain in src for domain in ["i.ibb.co", "i.imgur.com"]):
                    if src.startswith("//"):
                        return "https:" + src
                    if src.startswith("http"):
                        return src
        except Exception as e:
            print(f"[DonationImageDB] extract_direct_image_url error: {e}")
        return None

    def download_image_as_base64(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Скачивает картинку и возвращает (image_b64, image_mime)
        image_b64 = base64 string (без data: префикса)
        """
        max_attempts = 5
        base_delay = 1

        for attempt in range(max_attempts):
            try:
                direct_url = url

                # ibb/imgur short links -> вытянуть og:image
                if any(domain in url for domain in ["ibb.co", "imgur.com"]):
                    if not any(domain in url for domain in ["i.ibb.co", "i.imgur.com"]):
                        extracted = self.extract_direct_image_url(url)
                        if extracted:
                            direct_url = extracted

                resp = requests.get(direct_url, timeout=15)
                resp.raise_for_status()
                content = resp.content

                ok, image_type = self.is_valid_image_content(content)
                if not ok:
                    print(f"[DonationImageDB] not an image: {direct_url}")
                    return None, None

                mime = self._mime_from_type(image_type, resp.headers.get("content-type", ""))

                b64 = base64.b64encode(content).decode("ascii")
                return b64, mime

            except RequestException as e:
                print(f"[DonationImageDB] download attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    return None, None
                time.sleep(base_delay * (2 ** attempt))
            except Exception as e:
                print(f"[DonationImageDB] download unexpected error: {e}")
                return None, None

        return None, None

    # ---------- parsing ----------

    def extract_image_url(self, message: str) -> Optional[str]:
        url_pattern = r"https?://[^\s<>\"]+"
        urls = re.findall(url_pattern, message or "")

        for url in urls:
            u = url.lower()

            # --- New: обработка allwebs ---
            if "allwebs.ru/image/" in u:
                # парсим страницу и берем ссылку Direct
                try:
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    html = r.text

                    # найти ссылку Direct (пример)
                    m = re.search(r'href="(https?://allwebs\.ru/images/[^\"]+\.(?:jpg|png|webp))"', html)
                    if m:
                        return m.group(1)
                except Exception as e:
                    print(f"[DonationImageDB] allwebs parsing failed: {e}")
                continue

            # --- старые домены ---
            image_domains = [
                "ibb.co", "imgur.com", "i.imgur.com",
                "cdn.discordapp.com", "gyazo.com",
                "postimg.cc", "imageban.ru",
            ]
            if any(domain in u for domain in image_domains):
                return url
            if u.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff")):
                return url

        return None

    def parse_and_add_donation(self, user: str, message: str, amount_user: str) -> Optional[int]:
        image_url = self.extract_image_url(message)
        image_b64 = None
        image_mime = None

        if image_url:
            image_b64, image_mime = self.download_image_as_base64(image_url)

        return self.add_donation(user, message, amount_user, image_b64, image_mime)

    # ---------- CRUD ----------

    def add_donation(
        self,
        user: str,
        message: str,
        amount_user: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> Optional[int]:
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO donations (user, message, amount_user, image_b64, image_mime)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user, message, amount_user, image_b64, image_mime),
            )
            donation_id = cur.lastrowid
            conn.commit()
            conn.close()
            return donation_id
        except Exception as e:
            print(f"[DonationImageDB] add_donation error: {e}")
            return None

    def delete_donation(self, donation_id: int) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM donations WHERE id = ?", (donation_id,))
        conn.commit()
        conn.close()

    def get_donation_by_id(self, donation_id: int):
        """
        Возвращаем tuple:
        (id, user, message, amount_user, has_image, created_at)
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                user,
                message,
                amount_user,
                CASE WHEN image_b64 IS NOT NULL AND image_b64 != '' THEN 1 ELSE 0 END AS has_image,
                created_at
            FROM donations
            WHERE id = ?
            """,
            (donation_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    def get_image_payload(self, donation_id: int) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Возвращает (raw_bytes, mime) по donation_id.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT image_b64, image_mime
            FROM donations
            WHERE id = ?
            """,
            (donation_id,),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return None, None

        b64, mime = row[0], row[1]
        if not b64:
            return None, None

        try:
            raw = base64.b64decode(b64)
            return raw, (mime or "image/jpeg")
        except Exception as e:
            print(f"[DonationImageDB] base64 decode error (id={donation_id}): {e}")
            return None, None

    # ---------- list / pagination ----------

    def get_all_donations(self):
        """
        Совместимость: возвращаем список tuple (id, user, message, amount_user, has_image, created_at)
        (новые сверху)
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                user,
                message,
                amount_user,
                CASE WHEN image_b64 IS NOT NULL AND image_b64 != '' THEN 1 ELSE 0 END AS has_image,
                created_at
            FROM donations
            ORDER BY created_at DESC
            """
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_donations_page(self, page: int, page_size: int):
        """
        (items, total) LIMIT/OFFSET
        items: list tuple (id, user, message, amount_user, has_image, created_at)
        """
        page = max(1, int(page))
        page_size = max(1, min(100, int(page_size)))
        offset = (page - 1) * page_size

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM donations")
        total = int(cur.fetchone()[0] or 0)

        cur.execute(
            """
            SELECT
                id,
                user,
                message,
                amount_user,
                CASE WHEN image_b64 IS NOT NULL AND image_b64 != '' THEN 1 ELSE 0 END AS has_image,
                created_at
            FROM donations
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        )
        items = cur.fetchall()
        conn.close()

        return items, total


# Глобальный экземпляр (как у тебя принято)
donation_image_db = DonationImageDB()
