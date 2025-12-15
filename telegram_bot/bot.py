"""
Telegram bot asosiy fayl
"""
import os
import django
from django.conf import settings

# Django ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geeks_crm.settings')
django.setup()

from telegram import Bot
from telegram.ext import Application
from .handlers import setup_handlers
import logging

logger = logging.getLogger(__name__)


def create_bot():
    """Bot yaratish"""
    token = settings.TELEGRAM_BOT_TOKEN
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return None
    
    application = Application.builder().token(token).build()
    
    # Handlers ni sozlash
    setup_handlers(application)
    
    return application


def run_polling():
    """Polling rejimida botni ishga tushirish"""
    from telegram import Update
    
    application = create_bot()
    
    if not application:
        logger.error("Bot yaratilmadi")
        return
    
    logger.info("Bot polling rejimida ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_webhook(webhook_url, port=None):
    """Webhook rejimida botni ishga tushirish"""
    application = create_bot()
    
    if not application:
        logger.error("Bot yaratilmadi")
        return
    
    application.bot.set_webhook(url=webhook_url)
    logger.info(f"Bot webhook rejimida ishga tushdi: {webhook_url}")
    
    if port:
        from telegram.ext import Updater
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )

