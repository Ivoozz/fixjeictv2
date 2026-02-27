import logging
import os
from typing import Optional

import resend
from sqlalchemy.orm import Session

from .config import settings
from .models import Lead, Message, Ticket, User

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Resend API"""

    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def _is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(settings.RESEND_API_KEY)

    def _send_email(self, to_email: str, subject: str, html_content: str) -> Optional[str]:
        """Send an email and return the message ID"""
        if not self._is_configured():
            logger.warning("Resend not configured - skipping email")
            return None

        from_email = settings.RESEND_FROM

        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        try:
            result = resend.Emails.send(params)
            logger.info(f"Email sent to {to_email}: {result.get('id')}")
            return result.get("id")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return None

    def send_magic_link(self, email: str, token: str, name: str) -> Optional[str]:
        """Send magic link for login"""
        login_url = f"{settings.APP_URL}/auth/verify/{token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Uw login link voor FixJeICT</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🔐 FixJeICT</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Welkom, {name}!</h2>
                <p>Klik op de onderstaande knop om in te loggen op uw FixJeICT account:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{login_url}" style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Inloggen</a>
                </div>
                <p style="font-size: 14px; color: #666;">
                    Of kopieer deze link naar uw browser:<br>
                    <a href="{login_url}" style="color: #667eea;">{login_url}</a>
                </p>
                <p style="font-size: 12px; color: #999; margin-top: 30px;">
                    Deze link is 24 uur geldig. Als u niet om deze link heeft gevraagd, kunt u dit bericht negeren.
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(email, "🔐 Uw login link voor FixJeICT", html_content)

    def send_ticket_created(self, ticket: Ticket, client_email: str) -> Optional[str]:
        """Send email notification when a ticket is created"""
        ticket_url = f"{settings.APP_URL}/tickets/{ticket.id}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nieuw ticket #{ticket.id}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📋 FixJeICT</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Nieuw ticket aangemaakt</h2>
                <p>Uw ticket is succesvol aangemaakt:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3 style="margin-top: 0;">#{ticket.id} - {ticket.title}</h3>
                    <p><strong>Status:</strong> {ticket.status}</p>
                    <p><strong>Prioriteit:</strong> {ticket.priority}</p>
                    <p style="margin-bottom: 0;"><strong>Beschrijving:</strong></p>
                    <p style="white-space: pre-wrap;">{ticket.description}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{ticket_url}" style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Bekijk ticket</a>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(client_email, f"📋 Nieuw ticket #{ticket.id}: {ticket.title}", html_content)

    def send_ticket_updated(self, ticket: Ticket, client_email: str, new_status: str) -> Optional[str]:
        """Send email notification when ticket status changes"""
        ticket_url = f"{settings.APP_URL}/tickets/{ticket.id}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Update ticket #{ticket.id}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🔄 FixJeICT</h1>
            </div>
            <div style="padding: 30px; status: #f9f9f9;">
                <h2>Ticket bijgewerkt</h2>
                <p>De status van uw ticket is gewijzigd:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3 style="margin-top: 0;">#{ticket.id} - {ticket.title}</h3>
                    <p><strong>Nieuwe status:</strong> {new_status}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{ticket_url}" style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Bekijk ticket</a>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(client_email, f"🔄 Update ticket #{ticket.id}: {ticket.title}", html_content)

    def send_message_notification(self, ticket: Ticket, message: Message, recipient_email: str) -> Optional[str]:
        """Send email notification when a new message is posted"""
        ticket_url = f"{settings.APP_URL}/tickets/{ticket.id}"
        sender_name = message.user.name if message.user else "FixJeICT"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nieuw bericht ticket #{ticket.id}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">💬 FixJeICT</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Nieuw bericht</h2>
                <p>Er is een nieuw bericht geplaatst op uw ticket:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3 style="margin-top: 0;">#{ticket.id} - {ticket.title}</h3>
                    <p><strong>Van:</strong> {sender_name}</p>
                    <p style="margin-bottom: 0;"><strong>Bericht:</strong></p>
                    <p style="white-space: pre-wrap;">{message.content}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{ticket_url}" style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Bekijk ticket</a>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(recipient_email, f"💬 Nieuw bericht ticket #{ticket.id}: {ticket.title}", html_content)

    def send_lead_notification(self, lead: Lead) -> Optional[str]:
        """Send email notification for new lead"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nieuwe lead: {lead.name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📧 FixJeICT</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Nieuwe lead</h2>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <p><strong>Naam:</strong> {lead.name}</p>
                    <p><strong>Email:</strong> {lead.email}</p>
                    <p><strong>Bedrijf:</strong> {lead.company or 'N/A'}</p>
                    <p><strong>Telefoon:</strong> {lead.phone or 'N/A'}</p>
                    <p style="margin-bottom: 0;"><strong>Bericht:</strong></p>
                    <p style="white-space: pre-wrap;">{lead.message or 'Geen bericht'}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send to admin email (using RESEND_FROM as admin email)
        return self._send_email(settings.RESEND_FROM, f"📧 Nieuwe lead: {lead.name}", html_content)


# Global email service instance
email_service = EmailService()
