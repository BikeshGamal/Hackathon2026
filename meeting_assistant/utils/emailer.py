import smtplib
import json
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "team_config.json"

SMTP_PRESETS = {
    "Gmail":           {"host": "smtp.gmail.com",        "port": 587},
    "Outlook/Hotmail": {"host": "smtp.office365.com",    "port": 587},
    "Office 365":      {"host": "smtp.office365.com",    "port": 587},
    "Yahoo":           {"host": "smtp.mail.yahoo.com",   "port": 587},
    "Zoho":            {"host": "smtp.zoho.com",         "port": 587},
    "Custom":          {"host": "",                      "port": 587},
}


def load_team_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "sender_name": "", "sender_email": "", "smtp_password": "",
        "smtp_provider": "Gmail", "smtp_host": "smtp.gmail.com",
        "smtp_port": 587, "team_members": [],
    }


def save_team_config(config: dict):
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_email_html(notes: dict, meeting_time: str, sender_name: str) -> str:
    def rows(items, bullet):
        if not items:
            return "<p style='color:#888;font-size:13px;margin:0;'>None</p>"
        return "".join(
            f"<div style='padding:7px 0;border-bottom:1px solid #f0f0f0;"
            f"font-size:14px;color:#333;'>"
            f"<span style='color:#0d9488;margin-right:8px;'>{bullet}</span>{item}</div>"
            for item in items
        )

    kw = "".join(
        f"<span style='background:#f0fdfa;border:1px solid #99f6e4;color:#0d9488;"
        f"font-size:12px;padding:3px 10px;border-radius:100px;margin:2px;"
        f"display:inline-block;'>{k}</span>"
        for k in notes.get("keywords", [])
    )
    summary = notes.get("summary", "No summary available.").replace("\n", "<br>")

    def section(title, body):
        return (
            f"<div style='margin-bottom:20px;'>"
            f"<div style='font-size:10px;font-weight:600;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:#0d9488;padding-bottom:5px;"
            f"border-bottom:2px solid #ccfbf1;margin-bottom:8px;'>{title}</div>"
            f"{body}</div>"
        )

    return (
        f"<div style='font-family:Segoe UI,Arial,sans-serif;max-width:660px;margin:0 auto;'>"
        f"<div style='background:#0d9488;padding:24px 28px;border-radius:10px 10px 0 0;'>"
        f"<div style='font-size:20px;font-weight:600;color:#fff;'>Meeting Notes</div>"
        f"<div style='font-size:12px;color:#99f6e4;margin-top:3px;'>{meeting_time}</div>"
        f"</div>"
        f"<div style='background:#fafafa;padding:24px 28px;border:1px solid #e5e7eb;"
        f"border-top:none;border-radius:0 0 10px 10px;'>"
        + section("Summary", f"<p style='font-size:14px;line-height:1.7;color:#374151;margin:0;'>{summary}</p>")
        + section("Key Decisions", rows(notes.get("decisions", []), "&#9670;"))
        + section("Action Items", rows(notes.get("action_items", []), "&rarr;"))
        + (section("Key Topics", kw) if kw else "")
        + f"<div style='margin-top:20px;padding-top:12px;border-top:1px solid #e5e7eb;"
        f"font-size:11px;color:#9ca3af;text-align:center;'>"
        f"Sent by <strong>{sender_name}</strong> via MeetMind</div>"
        f"</div></div>"
    )


def test_smtp_connection(config: dict) -> tuple:
    """Test SMTP connection and login without sending any email."""
    try:
        with smtplib.SMTP(config["smtp_host"], int(config["smtp_port"]), timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config["sender_email"], config["smtp_password"])
        return True, "Connection successful!"
    except smtplib.SMTPAuthenticationError:
        return False, "Wrong email or password. Check credentials."
    except smtplib.SMTPConnectError as e:
        return False, f"Cannot connect to {config['smtp_host']}:{config['smtp_port']} — {e}"
    except TimeoutError:
        return False, f"Connection timed out. Check SMTP host and port."
    except Exception as e:
        return False, f"Error: {traceback.format_exc()}"


def send_meeting_email(
    config: dict,
    notes: dict,
    meeting_time: str,
    recipient_emails: list,
    subject: str = None,
) -> tuple:
    if not config.get("sender_email") or not config.get("smtp_password"):
        return False, "Sender email or password not set. Click Edit Setup."
    if not recipient_emails:
        return False, "No recipients selected."
    if not config.get("smtp_host"):
        return False, "SMTP host not configured."

    subject = subject or f"Meeting Notes — {meeting_time}"
    html_body = build_email_html(notes, meeting_time, config.get("sender_name", "MeetMind"))

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{config.get('sender_name', '')} <{config['sender_email']}>"
        msg["To"]      = ", ".join(recipient_emails)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(config["smtp_host"], int(config["smtp_port"]), timeout=15) as server:
            server.set_debuglevel(0)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config["sender_email"], config["smtp_password"])
            server.sendmail(config["sender_email"], recipient_emails, msg.as_string())

        return True, f"Sent to {len(recipient_emails)} recipient(s) successfully."

    except smtplib.SMTPAuthenticationError:
        return False, "Login failed — wrong email or password."
    except smtplib.SMTPRecipientsRefused as e:
        return False, f"Recipient refused: {e}"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except TimeoutError:
        return False, "Connection timed out. Check your internet or SMTP settings."
    except Exception:
        return False, f"Unexpected error:\n{traceback.format_exc()}"