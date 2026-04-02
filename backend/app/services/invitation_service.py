import secrets
import string
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models import Event, Invitation
from app.schemas.invitation import GuestCreate, InvitationOut, BulkInviteResponse
from app.services.gigachat_client import make_client
from app.core.config import settings


class InvitationService:
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def generate_token() -> str:
        """Генерация уникального токена для приглашения"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    def generate_ai_invitation_message(
        self,
        event: Event,
        guest_name: Optional[str],
        guest_email: str,
        custom_template: Optional[str] = None,
        is_birthday_person: bool = False
    ) -> dict:
        """Генерация персонализированного сообщения приглашения через AI"""
        
        guest_display = guest_name or guest_email.split('@')[0]
        
        # Для именинника - другое системное сообщение
        if is_birthday_person:
            system_prompt = (
                "Ты — дружелюбный помощник по организации мероприятий. "
                "Твоя задача — написать тёплое персонализированное сообщение для именинника. "
                "Это его праздник! Сообщение должно быть на русском языке, дружелюбным и поздравительным. "
                "Включи призыв к действию для подтверждения участия и упомяни, что он может добавить подарки в вишлист."
            )
        else:
            system_prompt = (
                "Ты — дружелюбный помощник по организации мероприятий. "
                "Твоя задача — написать тёплое, персонализированное приглашение на мероприятие. "
                "Сообщение должно быть на русском языке, дружелюбным, но не слишком formal. "
                "Включи ключевые детали мероприятия и призыв к действию (подтвердить участие)."
            )
        
        event_details = f"""
Мероприятие: {event.title}
Дата: {event.event_date or 'уточняется'}
Город: {event.city or 'уточняется'}
Формат: {event.format or 'уточняется'}
Описание: {event.notes or ''}
"""
        
        # Для именинника - другой промпт
        if is_birthday_person:
            if custom_template:
                user_prompt = f"""
Напиши приглашение для именинника по имени {guest_display} ({guest_email}).

Детали мероприятия:
{event_details}

Используй этот шаблон как основу, но адаптируй:
{custom_template}

Сгенерируй:
1. Тему письма (краткую, привлекающую внимание)
2. Текст приглашения (2-4 абзаца, тёплый тон, поздравительный)
3. Упомяни, что он может добавить подарки в вишлист для гостей
4. Призыв к действию для подтверждения участия
"""
            else:
                user_prompt = f"""
Напиши приглашение для именинника по имени {guest_display} ({guest_email}).

Детали мероприятия:
{event_details}

Сгенерируй:
1. Тему письма (краткую, поздравительную)
2. Текст приглашения (2-4 абзаца, тёплый тон, персонализированное поздравление)
3. Упомяни, что он может добавить подарки в вишлист на странице подтверждения
4. Призыв к действию для подтверждения участия
"""
        else:
            if custom_template:
                user_prompt = f"""
Напиши приглашение для гостя по имени {guest_display} ({guest_email}).

Детали мероприятия:
{event_details}

Используй этот шаблон как основу, но адаптируй:
{custom_template}

Сгенерируй:
1. Тему письма (краткую, привлекающую внимание)
2. Текст приглашения (2-4 абзаца, тёплый тон)
3. Призыв к действию для подтверждения участия
"""
            else:
                user_prompt = f"""
Напиши приглашение для гостя по имени {guest_display} ({guest_email}).

Детали мероприятия:
{event_details}

Сгенерируй:
1. Тему письма (краткую, привлекающую внимание)
2. Текст приглашения (2-4 абзаца, дружелюбный тон, персонализированное обращение)
3. Призыв к действию для подтверждения участия
4. Предложение задать вопросы организатору
"""
        
        try:
            with make_client() as giga:
                response = giga.chat({
                    "model": settings.GIGACHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.8,
                })
            
            ai_response = response.choices[0].message.content
            
            # Парсим ответ AI для извлечения темы и тела письма
            lines = ai_response.strip().split('\n')
            subject = "Приглашение на мероприятие"
            body = ai_response
            
            # Ищем тему в ответе
            for i, line in enumerate(lines):
                if 'тема:' in line.lower() or 'subject:' in line.lower():
                    subject = line.split(':', 1)[-1].strip()
                    body = '\n'.join(lines[i+1:]).strip()
                    break
                elif i == 0 and len(line) < 100 and not line.startswith('Привет'):
                    # Первая строка короткая - вероятно тема
                    subject = line.strip()
                    body = '\n'.join(lines[1:]).strip()
            
            return {
                'subject': subject,
                'body': body,
                'full_response': ai_response
            }
            
        except Exception as e:
            # Fallback сообщение если AI недоступен
            if is_birthday_person:
                return {
                    'subject': f"Приглашение на {event.title}",
                    'body': f"""Привет, {guest_display}!

Приглашаю тебя на {event.title} — это твой праздник! 🎂

Дата: {event.event_date or 'уточняется'}
Место: {event.city or 'уточняется'}

Будем рады отпраздновать с тобой! После подтверждения участия ты сможешь добавить подарки в вишлист, которые хотел бы получить.

С наилучшими пожеланиями,
Организатор
""",
                    'full_response': None,
                    'error': str(e)
                }
            else:
                return {
                    'subject': f"Приглашение на {event.title}",
                    'body': f"""Привет, {guest_display}!

Приглашаю тебя на {event.title}.

Дата: {event.event_date or 'уточняется'}
Место: {event.city or 'уточняется'}

Буду рад(а) видеть тебя! Пожалуйста, подтверди участие.

С наилучшими пожеланиями,
Организатор
""",
                    'full_response': None,
                    'error': str(e)
                }
    
    def send_email_invitation(self, invitation: Invitation, subject: str, body: str) -> bool:
        """Отправка приглашения по email через SMTP"""
        
        # Проверяем настройки SMTP
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"[EMAIL ERROR] SMTP не настроен. Установите SMTP_USER и SMTP_PASSWORD в .env")
            invitation.error_message = "SMTP не настроен"
            return False
        
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_FROM or settings.SMTP_USER
            msg['To'] = invitation.guest_email
            
            # Добавляем ссылку для подтверждения
            rsvp_link = f"http://localhost:5173/invitations/rsvp/{invitation.token}"
            full_body = f"""{body}

---
Подтвердить участие: {rsvp_link}
"""
            
            # HTML версия
            html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        {full_body.replace(chr(10), '<br>')}
        <br><br>
        <a href="{rsvp_link}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
            Подтвердить участие
        </a>
    </div>
</body>
</html>"""
            
            msg.attach(MIMEText(full_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Отправляем через SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"[EMAIL SENT] To: {invitation.guest_email}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"[EMAIL ERROR] Failed to send to {invitation.guest_email}: {error_msg}")
            invitation.error_message = f"SMTP Error: {error_msg[:200]}"
            return False
    
    def send_telegram_invitation(self, invitation: Invitation, message: str) -> bool:
        """Отправка приглашения через Telegram (заглушка)"""
        # TODO: Интеграция с Telegram Bot API
        print(f"[TELEGRAM] To: {invitation.guest_phone or invitation.guest_email}")
        print(f"[TELEGRAM] Message: {message[:200]}...")
        return True
    
    def create_and_send_invitations(
        self,
        event: Event,
        guests: List[GuestCreate],
        message_template: Optional[str] = None,
        send_via: str = "email",
        ai_personalization: bool = True,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> BulkInviteResponse:
        """Создание и отправка приглашений группе гостей"""
        
        total = len(guests)
        created = 0
        sent = 0
        failed = 0
        errors = []
        invitations = []
        
        for guest in guests:
            try:
                # Проверяем, нет ли уже приглашения для этого email
                existing = self.db.query(Invitation).filter(
                    Invitation.event_id == event.id,
                    Invitation.guest_email == guest.email
                ).first()
                
                if existing:
                    errors.append(f"{guest.email}: уже есть приглашение")
                    failed += 1
                    continue
                
                # Создаем приглашение
                token = self.generate_token()
                invitation = Invitation(
                    event_id=event.id,
                    guest_email=guest.email,
                    guest_name=guest.name,
                    guest_phone=guest.phone,
                    # is_birthday_person=guest.is_birthday_person,
                    token=token,
                    status='pending'
                )
                self.db.add(invitation)
                self.db.flush()
                created += 1
                
                # Генерируем сообщение
                if ai_personalization:
                    message_data = self.generate_ai_invitation_message(
                        event=event,
                        guest_name=guest.name,
                        guest_email=guest.email,
                        custom_template=message_template
                        # is_birthday_person=guest.is_birthday_person
                    )
                else:
                    message_data = {
                        'subject': f"Приглашение на {event.title}",
                        'body': message_template or f"Приглашаем вас на {event.title}!",
                        'full_response': None
                    }
                
                invitation.message_content = message_data['body']
                
                # Отправляем
                success = False
                if send_via == "email":
                    success = self.send_email_invitation(
                        invitation,
                        message_data['subject'],
                        message_data['body']
                    )
                elif send_via == "telegram":
                    success = self.send_telegram_invitation(
                        invitation,
                        message_data['body']
                    )
                
                if success:
                    invitation.status = 'sent'
                    invitation.sent_at = datetime.utcnow()
                    invitation.sent_via = send_via
                    sent += 1
                else:
                    invitation.error_message = "Ошибка отправки"
                    errors.append(f"{guest.email}: ошибка отправки")
                    failed += 1
                
                self.db.commit()
                self.db.refresh(invitation)
                invitations.append(InvitationOut.from_orm(invitation))
                
            except Exception as e:
                errors.append(f"{guest.email}: {str(e)}")
                failed += 1
                self.db.rollback()
        
        return BulkInviteResponse(
            total=total,
            created=created,
            sent=sent,
            failed=failed,
            errors=errors,
            invitations=invitations
        )
    
    def resend_invitation(self, invitation: Invitation, background_tasks: Optional[BackgroundTasks] = None) -> bool:
        """Повторная отправка приглашения"""
        try:
            if invitation.message_content:
                success = self.send_email_invitation(
                    invitation,
                    f"Напоминание: приглашение на мероприятие",
                    invitation.message_content
                )
            else:
                # Регенерируем сообщение если его нет
                event = self.db.query(Event).filter(Event.id == invitation.event_id).first()
                message_data = self.generate_ai_invitation_message(
                    event=event,
                    guest_name=invitation.guest_name,
                    guest_email=invitation.guest_email
                )
                invitation.message_content = message_data['body']
                success = self.send_email_invitation(
                    invitation,
                    message_data['subject'],
                    message_data['body']
                )
            
            if success:
                invitation.status = 'sent'
                invitation.sent_at = datetime.utcnow()
                self.db.commit()
                return True
            else:
                invitation.error_message = "Ошибка повторной отправки"
                self.db.commit()
                return False
                
        except Exception as e:
            invitation.error_message = str(e)
            self.db.commit()
            return False
