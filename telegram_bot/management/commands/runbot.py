"""
Django management command: Telegram botni ishga tushirish
Usage: python manage.py runbot
"""
from django.core.management.base import BaseCommand
from telegram_bot.bot import run_polling


class Command(BaseCommand):
    help = 'Telegram botni polling rejimida ishga tushirish'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Telegram bot ishga tushmoqda...'))
        run_polling()

