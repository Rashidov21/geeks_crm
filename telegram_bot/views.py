"""
Telegram bot webhook views
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Global application instance
_application = None


def get_application():
    """Application instance olish (singleton)"""
    global _application
    if _application is None:
        from telegram_bot.bot import create_bot
        _application = create_bot()
    return _application


@csrf_exempt
def webhook(request):
    """
    Telegram webhook endpoint
    """
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    
    try:
        from telegram import Update
        
        application = get_application()
        
        if not application:
            return HttpResponse('Bot not configured', status=500)
        
        # Update ni qayta ishlash
        update = Update.de_json(json.loads(request.body), application.bot)
        application.process_update(update)
        
        return HttpResponse('OK')
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return HttpResponse('Error', status=500)
