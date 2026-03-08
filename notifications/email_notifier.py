# notifications/email_notifier.py
import smtplib
import json
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from loguru import logger
from core.database import Listing


class EmailNotifier:
    def __init__(self, host: str, port: int, user: str, password: str,
                 email_from: str, email_to: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.email_from = email_from
        self.email_to = email_to

    def format_html(self, listing: Listing) -> str:
        if listing.price:
            price_str = f"{listing.price:,} Kč".replace(",", "&nbsp;")
        else:
            price_str = "Cena neuvedena"
        images = []
        if listing.images_json:
            try:
                images = json.loads(listing.images_json)
            except (ValueError, TypeError):
                pass
        img_html = (
            f'<img src="{images[0]}" style="max-width:500px;border-radius:8px" alt="foto"/><br/>'
            if images else ""
        )
        desc = (listing.description or "")[:300]
        return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><title>{listing.title}</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
  <h2 style="color:#2c5f2e">🏠 {listing.title}</h2>
  {img_html}
  <p><strong>Cena:</strong> {price_str}</p>
  <p><strong>Dispozice:</strong> {listing.size_category or "N/A"}</p>
  <p><strong>Lokalita:</strong> {listing.location or "N/A"}</p>
  <p><strong>Popis:</strong> {desc}</p>
  <p><a href="{listing.url}" style="background:#2c5f2e;color:white;padding:10px 20px;
     border-radius:5px;text-decoration:none">Zobrazit inzerát</a></p>
  <hr/>
  <small>Zdroj: {listing.source} | Nalezeno: {datetime.now().strftime("%d.%m.%Y %H:%M")}</small>
</body>
</html>"""

    def send(self, listing: Listing) -> bool:
        try:
            if listing.price:
                subject = f"[BytoHled] {listing.title} — {listing.price:,} Kč".replace(",", " ")
            else:
                subject = f"[BytoHled] {listing.title}"
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = self.email_to
            msg.attach(MIMEText(self.format_html(listing), "html", "utf-8"))
            with smtplib.SMTP(self.host, self.port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.user, self.password)
                smtp.sendmail(self.email_from, self.email_to, msg.as_string())
            logger.info(f"[email] Sent for {listing.url}")
            return True
        except Exception as e:
            logger.error(f"[email] Send failed: {e}")
            return False
