import os
import httpx


class TelegramNotifier:
    def __init__(self) -> None:
        self.token = os.environ["TELEGRAM_BOT_TOKEN"]
        self.chat_id = os.environ["TELEGRAM_CHAT_ID"]
        self._api = f"https://api.telegram.org/bot{self.token}"

    def send_listing(self, listing_data: dict, dashboard_url: str = "") -> None:
        price_raw = listing_data.get("price")
        if price_raw is not None:
            price_str = f"{price_raw:,} Kč".replace(",", " ")
        else:
            price_str = "neuvedena"

        price_type_label = "Prodej" if listing_data.get("price_type") == "sale" else "Pronájem"
        disposition = listing_data.get("disposition") or "?"
        area = listing_data.get("area_m2") or "?"
        address = listing_data.get("address") or ""
        source = listing_data.get("source", "").capitalize()

        text = (
            f"🏠 [{disposition} | {area}m² | {price_str}]\n"
            f"{price_type_label} — {address}\n\n"
            f"💰 Cena: {price_str}\n"
            f"🔗 Zdroj: {source}"
        )

        buttons = []
        if listing_data.get("url"):
            buttons.append({"text": "Zobrazit inzerát", "url": listing_data["url"]})
        if dashboard_url:
            buttons.append({"text": "Dashboard", "url": dashboard_url})

        payload: dict = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": [buttons]}

        httpx.post(f"{self._api}/sendMessage", json=payload, timeout=10)
