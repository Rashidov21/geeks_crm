"""
Script to check URL patterns and their corresponding views
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geeks_crm.settings')
django.setup()

from django.urls import get_resolver
from django.conf import settings
import importlib

# #region agent log
import json
log_path = r'c:\Users\rashi\Documents\GitHub\geeks_crm\.cursor\debug.log'
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({
        'location': 'check_urls_views.py:start',
        'message': 'Starting URL and view validation',
        'timestamp': django.utils.timezone.now().isoformat(),
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'A'
    }) + '\n')
# #endregion

errors = []
warnings = []

try:
    resolver = get_resolver()
    
    # #region agent log
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            'location': 'check_urls_views.py:resolver',
            'message': 'Got URL resolver',
            'data': {'url_count': len(resolver.url_patterns)},
            'timestamp': django.utils.timezone.now().isoformat(),
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A'
        }) + '\n')
    # #endregion
    
    def check_url_patterns(patterns, prefix=''):
        for pattern in patterns:
            try:
                if hasattr(pattern, 'url_patterns'):
                    check_url_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
                elif hasattr(pattern, 'callback'):
                    view = pattern.callback
                    view_name = getattr(view, '__name__', str(view))
                    url_name = pattern.name
                    full_path = prefix + str(pattern.pattern)
                    
                    # #region agent log
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            'location': 'check_urls_views.py:check_pattern',
                            'message': 'Checking URL pattern',
                            'data': {'url_name': url_name, 'view_name': view_name, 'path': full_path},
                            'timestamp': django.utils.timezone.now().isoformat(),
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'A'
                        }) + '\n')
                    # #endregion
                    
                    # Check if view is callable
                    if not callable(view):
                        errors.append(f"URL '{full_path}' ({url_name}) has non-callable view: {view}")
                    else:
                        # Check if view class exists and has required methods
                        if hasattr(view, 'view_class'):
                            view_class = view.view_class
                            # Check common methods
                            if hasattr(view_class, 'get') and not hasattr(view_class, 'get'):
                                warnings.append(f"View {view_name} might be missing get method")
            except Exception as e:
                errors.append(f"Error checking pattern {pattern}: {str(e)}")
                # #region agent log
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'location': 'check_urls_views.py:error',
                        'message': 'Error checking URL pattern',
                        'data': {'error': str(e), 'pattern': str(pattern)},
                        'timestamp': django.utils.timezone.now().isoformat(),
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'A'
                    }) + '\n')
                # #endregion
    
    check_url_patterns(resolver.url_patterns)
    
    # #region agent log
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            'location': 'check_urls_views.py:complete',
            'message': 'URL validation complete',
            'data': {'errors': len(errors), 'warnings': len(warnings)},
            'timestamp': django.utils.timezone.now().isoformat(),
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A'
        }) + '\n')
    # #endregion
    
    print("=" * 80)
    print("URL AND VIEW VALIDATION REPORT")
    print("=" * 80)
    print(f"\nErrors found: {len(errors)}")
    print(f"Warnings found: {len(warnings)}")
    
    if errors:
        print("\n" + "=" * 80)
        print("ERRORS:")
        print("=" * 80)
        for error in errors:
            print(f"  ❌ {error}")
    
    if warnings:
        print("\n" + "=" * 80)
        print("WARNINGS:")
        print("=" * 80)
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    if not errors and not warnings:
        print("\n[OK] No errors or warnings found!")
    
except Exception as e:
    # #region agent log
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            'location': 'check_urls_views.py:fatal',
            'message': 'Fatal error in validation',
            'data': {'error': str(e)},
            'timestamp': django.utils.timezone.now().isoformat(),
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A'
        }) + '\n')
    # #endregion
    print(f"FATAL ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

