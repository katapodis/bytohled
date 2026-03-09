# notifications/telegram.py
import asyncio
import json
from datetime import datetime
from typing import Optional
from loguru import logger
from core.database import Listing


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._api_base = f"https://api.telegram.org/bot{bot_token}"

    def format_message(self, listing: Listing) -> str:
        if listing.price:
            price_str = f"{listing.price:,} Kč".replace(",", " ")
        else:
            price_str = "Cena neuvedena ⚠️"
        desc = (listing.description or "")[:300]
        if len(listing.description or "") > 300:
            desc += "..."
        return (
            f"🏠 *{listing.title}*\n\n"
            f"💰 {price_str}\n"
            f"📐 {listing.size_category or 'N/A'} | 📍 {listing.location or 'N/A'}\n\n"
            f"{desc}\n\n"
            f"🔗 [Odkaz na inzerát]({listing.url})\n"
            f"📊 Zdroj: `{listing.source}` | 🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

    def send(self, listing: Listing) -> bool:
        """Send notification. Returns True on success."""
        try:
            return asyncio.run(self._send_async(listing))
        except Exception as e:
            logger.error(f"[telegram] Send error: {e}")
            return False

    async def _send_async(self, listing: Listing) -> bool:
        import aiohttp
        import ssl
        import certifi
        text = self.format_message(listing)
        images = []
        if listing.images_json:
            try:
                images = json.loads(listing.images_json)
            except (ValueError, TypeError):
                pass
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                if images:
                    ok = await self._send_photo(session, text, images[0])
                    if ok:
                        return True
                return await self._send_text(session, text)
        except Exception as e:
            logger.error(f"[telegram] HTTP error: {e}")
            return False

    async def _send_photo(self, session, caption: str, photo_url: str) -> bool:
        url = f"{self._api_base}/sendPhoto"
        payload = {
            "chat_id": self.chat_id,
            "photo": photo_url,
            "caption": caption[:1024],
            "parse_mode": "Markdown",
        }
        async with session.post(url, json=payload) as resp:
            try:
                result = await resp.json()
                if result.get("ok"):
                    return True
            except Exception:
                pass
            logger.warning(f"[telegram] sendPhoto failed: {resp.status}")
            return False

    async def _send_text(self, session, text: str) -> bool:
        url = f"{self._api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text[:4096],
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            if result.get("ok"):
                return True
            logger.error(f"[telegram] sendMessage failed: {result}")
            return False
