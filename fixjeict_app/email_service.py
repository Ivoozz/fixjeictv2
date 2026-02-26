import os
import resend
from datetime import datetime, timedelta
from flask import current_app


class EmailService:
    def __init__(self):
        resend.api_key = os.environ.get('RESEND_API_KEY')

    def _is_configured(self):
        return bool(os.environ.get('RESEND_API_KEY'))

    def send_magic_link(self, email, token, name):
        if not self._is_configured():
            current_app.logger.warning('Resend not configured - skipping magic link email')
            return None

        from_email = os.environ.get('RESEND_FROM', 'noreply@fixjeict.nl')
        login_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/auth/verify/{token}"

        params = {
            'from': from_email,
            'to': [email],
            'subject': '🔐 Uw login link voor FixJeICT',
            'html': self._magic_link_template(name, login_url)
        }

        try:
            result = resend.Emails.send(params)
            return result.get('id')
        except Exception as e:
            current_app.logger.error(f'Failed to send magic link: {e}')
            return None

    def send_ticket_created(self, ticket, client_email):
        if not self._is_configured():
            return None

        from_email = os.environ.get('RESEND_FROM', 'noreply@fixjeict.nl')
        ticket_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/tickets/{ticket.id}"

        params = {
            'from': from_email,
            'to': [client_email],
            'subject': f'📋 Nieuw ticket #{ticket.id}: {ticket.title}',
            'html': self._ticket_created_template(ticket, ticket_url)
        }

        try:
            result = resend.Emails.send(params)
            return result.get('id')
        except Exception as e:
            current_app.logger.error(f'Failed to send ticket email: {e}')
            return None

    def send_ticket_updated(self, ticket, client_email, status):
        if not self._is_configured():
            return None

        from_email = os.environ.get('RESEND_FROM', 'noreply@fixjeict.nl')
        ticket_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/tickets/{ticket.id}"

        params = {
            'from': from_email,
            'to': [client_email],
            'subject': f'🔄 Update ticket #{ticket.id}: {ticket.title}',
            'html': self._ticket_updated_template(ticket, ticket_url, status)
        }

        try:
            result = resend.Emails.send(params)
            return result.get('id')
        except Exception as e:
            current_app.logger.error(f'Failed to send ticket update email: {e}')
            return None

    def send_message_notification(self, ticket, message, recipient_email):
        if not self._is_configured():
            return None

        from_email = os.environ.get('RESEND_FROM', 'noreply@fixjeict.nl')
        ticket_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/tickets/{ticket.id}"

        params = {
            'from': from_email,
            'to': [recipient_email],
            'subject': f'💬 Nieuw bericht ticket #{ticket.id}: {ticket.title}',
            'html': self._message_template(ticket, message, ticket_url)
        }

        try:
            result = resend.Emails.send(params)
            return result.get('id')
        except Exception as e:
            current_app.logger.error(f'Failed to send message email: {e}')
            return None

    def send_lead_notification(self, lead):
        if not self._is_configured():
            return None

        from_email = os.environ.get('RESEND_FROM', 'noreply@fixjeict.nl')

        params = {
            'from': from_email,
            'to': [from_email],
            'subject': f'🎯 Nieuwe lead van {lead.name}',
            'html': self._lead_template(lead)
        }

        try:
            result = resend.Emails.send(params)
            return result.get('id')
        except Exception as e:
            current_app.logger.error(f'Failed to send lead email: {e}')
            return None

    def _magic_link_template(self, name, login_url):
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; margin-top: 20px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 FixJeICT Login</h1>
    </div>
    <div class="content">
        <p>Hoi {name},</p>
        <p>Klik op de onderstaande knop om in te loggen op uw FixJeICT account:</p>
        <center><a href="{login_url}" class="button">Inloggen</a></center>
        <p style="margin-top: 30px; font-size: 14px; color: #666;">
            Of gebruik deze link:<br>
            <a href="{login_url}" style="color: #667eea;">{login_url}</a>
        </p>
        <p style="margin-top: 20px; font-size: 14px; color: #666;">
            Deze link is 24 uur geldig.
        </p>
    </div>
    <div class="footer">
        <p>FixJeICT - Uw ICT partner</p>
    </div>
</body>
</html>
'''

    def _ticket_created_template(self, ticket, ticket_url):
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .ticket-info {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .label {{ font-weight: bold; color: #667eea; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Nieuw Ticket Aangemaakt</h1>
    </div>
    <div class="content">
        <p>Uw nieuwe ticket is succesvol aangemaakt:</p>
        <div class="ticket-info">
            <p><span class="label">Ticket #:</span> {ticket.id}</p>
            <p><span class="label">Onderwerp:</span> {ticket.title}</p>
            <p><span class="label">Status:</span> {ticket.status}</p>
        </div>
        <center><a href="{ticket_url}" class="button">Bekijk Ticket</a></center>
        <p style="margin-top: 20px; font-size: 14px; color: #666;">
            We nemen zo snel mogelijk contact met u op.
        </p>
    </div>
</body>
</html>
'''

    def _ticket_updated_template(self, ticket, ticket_url, status):
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .ticket-info {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .status-badge {{ display: inline-block; background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 Ticket Update</h1>
    </div>
    <div class="content">
        <p>Uw ticket is bijgewerkt:</p>
        <div class="ticket-info">
            <p><span class="label">Ticket #:</span> {ticket.id}</p>
            <p><span class="label">Onderwerp:</span> {ticket.title}</p>
            <p><span class="label">Nieuwe status:</span> <span class="status-badge">{status}</span></p>
        </div>
        <center><a href="{ticket_url}" class="button">Bekijk Ticket</a></center>
    </div>
</body>
</html>
'''

    def _message_template(self, ticket, message, ticket_url):
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .message {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #667eea; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💬 Nieuw Bericht</h1>
    </div>
    <div class="content">
        <p>Er is een nieuw bericht geplaatst op ticket #{ticket.id}:</p>
        <p><strong>{ticket.title}</strong></p>
        <div class="message">
            {message.content.replace(chr(10), '<br>')}
        </div>
        <center><a href="{ticket_url}" class="button">Bekijk Ticket</a></center>
    </div>
</body>
</html>
'''

    def _lead_template(self, lead):
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .lead-info {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .label {{ font-weight: bold; color: #667eea; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Nieuwe Lead</h1>
    </div>
    <div class="content">
        <div class="lead-info">
            <p><span class="label">Naam:</span> {lead.name}</p>
            <p><span class="label">Email:</span> {lead.email}</p>
            <p><span class="label">Bedrijf:</span> {lead.company or '-'}</p>
            <p><span class="label">Telefoon:</span> {lead.phone or '-'}</p>
            <p><span class="label">Bericht:</span></p>
            <p>{lead.message or '-'}</p>
        </div>
    </div>
</body>
</html>
'''


email_service = EmailService()
