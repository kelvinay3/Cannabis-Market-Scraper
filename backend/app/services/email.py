import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


def _html_email(subject: str, html_body: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg.attach(MIMEText(html_body, "html"))
    return msg


async def send_email(to: str, subject: str, html_body: str) -> bool:
    if settings.resend_api_key:
        return await _send_via_resend(to, subject, html_body)
    return _send_via_print(to, subject, html_body)


async def _send_via_resend(to: str, subject: str, html_body: str) -> bool:
    try:
        import resend
        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": f"{settings.email_from_name} <{settings.email_from}>",
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        return True
    except Exception as e:
        print(f"[email] Resend error: {e}")
        return False


def _send_via_print(to: str, subject: str, html_body: str) -> bool:
    print(f"\n{'='*60}")
    print(f"[EMAIL SIMULATION — add RESEND_API_KEY to send real emails]")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"Body (HTML stripped): {html_body[:300]}")
    print(f"{'='*60}\n")
    return True


def _base_template(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#F7F5F0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #DDD;">
    <div style="background:#15502A;padding:24px 32px;">
      <h1 style="margin:0;color:#fff;font-size:18px;font-weight:600;letter-spacing:0.5px;">NJ Cannabis Intel</h1>
    </div>
    <div style="padding:32px;">
      {content}
    </div>
    <div style="background:#F7F5F0;padding:16px 32px;border-top:1px solid #DDD;font-size:12px;color:#888;text-align:center;">
      NJ Cannabis Market Intelligence Platform &nbsp;|&nbsp; Unsubscribe
    </div>
  </div>
</body>
</html>
"""


async def send_password_reset_email(to: str, name: str, reset_link: str) -> bool:
    content = f"""
    <p style="color:#333;font-size:15px;">Hi {name or "there"},</p>
    <p style="color:#555;font-size:14px;line-height:1.6;">
      We received a request to reset your password. Click the button below to set a new one.
      This link expires in 60 minutes.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{reset_link}" style="background:#15502A;color:#fff;padding:14px 28px;border-radius:5px;text-decoration:none;font-size:15px;font-weight:600;display:inline-block;">
        Reset Password
      </a>
    </div>
    <p style="color:#888;font-size:12px;">If you didn't request this, you can ignore this email. Your password won't change.</p>
    <p style="color:#888;font-size:12px;">Or copy this link: <a href="{reset_link}" style="color:#15502A;">{reset_link}</a></p>
    """
    return await send_email(to, "Reset your NJ Cannabis Intel password", _base_template(content))


async def send_invite_email(to: str, invited_by: str, role: str, invite_link: str) -> bool:
    content = f"""
    <p style="color:#333;font-size:15px;">You've been invited!</p>
    <p style="color:#555;font-size:14px;line-height:1.6;">
      <strong>{invited_by}</strong> has invited you to join <strong>NJ Cannabis Intel</strong>
      as a <strong>{role.replace('_', ' ').title()}</strong>.
    </p>
    <p style="color:#555;font-size:14px;line-height:1.6;">
      Click the button below to create your account. This invite expires in 7 days.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{invite_link}" style="background:#15502A;color:#fff;padding:14px 28px;border-radius:5px;text-decoration:none;font-size:15px;font-weight:600;display:inline-block;">
        Accept Invitation
      </a>
    </div>
    <p style="color:#888;font-size:12px;">Or copy this link: <a href="{invite_link}" style="color:#15502A;">{invite_link}</a></p>
    """
    return await send_email(to, f"You're invited to NJ Cannabis Intel", _base_template(content))


async def send_deal_alert_email(to: str, name: str, alert_name: str, deals: list) -> bool:
    deals_html = "".join([
        f"""<div style="padding:12px 0;border-bottom:1px solid #EEE;">
          <strong style="color:#1C1C19;">{d.get('dispensary_name', '')}</strong>
          <span style="color:#888;font-size:12px;margin-left:8px;">{d.get('city', '')} · {d.get('county', '')}</span>
          <p style="margin:4px 0 0;color:#333;font-size:13px;">{d.get('title', '')}</p>
        </div>"""
        for d in deals[:10]
    ])
    content = f"""
    <p style="color:#333;font-size:15px;">Hi {name or 'there'} — your alert fired.</p>
    <p style="color:#555;font-size:13px;margin-bottom:16px;">Alert: <strong>{alert_name}</strong></p>
    {deals_html}
    <div style="text-align:center;margin:28px 0;">
      <a href="{settings.frontend_url}/deals" style="background:#15502A;color:#fff;padding:12px 24px;border-radius:5px;text-decoration:none;font-size:14px;font-weight:600;display:inline-block;">
        View All Deals
      </a>
    </div>
    """
    return await send_email(to, f"Alert: {alert_name} — New deals found", _base_template(content))
