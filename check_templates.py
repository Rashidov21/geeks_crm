"""
Script to check template syntax errors
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geeks_crm.settings')
django.setup()

from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.conf import settings
import glob
import json

# #region agent log
log_path = r'c:\Users\rashi\Documents\GitHub\geeks_crm\.cursor\debug.log'
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({
        'location': 'check_templates.py:start',
        'message': 'Starting template syntax validation',
        'timestamp': django.utils.timezone.now().isoformat(),
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'B'
    }) + '\n')
# #endregion

errors = []
warnings = []

# Find all template files
template_dirs = [os.path.join(settings.BASE_DIR, 'templates')]
template_files = []

for template_dir in template_dirs:
    if os.path.exists(template_dir):
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))

# #region agent log
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({
        'location': 'check_templates.py:found_templates',
        'message': 'Found template files',
        'data': {'count': len(template_files)},
        'timestamp': django.utils.timezone.now().isoformat(),
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'B'
    }) + '\n')
# #endregion

for template_file in template_files:
    try:
        rel_path = os.path.relpath(template_file, settings.BASE_DIR)
        
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'location': 'check_templates.py:check_template',
                'message': 'Checking template',
                'data': {'file': rel_path},
                'timestamp': django.utils.timezone.now().isoformat(),
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B'
            }) + '\n')
        # #endregion
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common syntax errors
        # 1. Unclosed tags
        open_tags = content.count('{%')
        close_tags = content.count('%}')
        if open_tags != close_tags:
            errors.append(f"{rel_path}: Mismatched template tags ({open_tags} open, {close_tags} close)")
        
        # 2. Unclosed blocks
        block_starts = content.count('{% block')
        block_ends = content.count('{% endblock')
        if block_starts != block_ends:
            errors.append(f"{rel_path}: Mismatched block tags ({block_starts} starts, {block_ends} ends)")
        
        # 3. Unclosed if statements
        if_starts = content.count('{% if')
        if_ends = content.count('{% endif')
        if if_starts != if_ends:
            errors.append(f"{rel_path}: Mismatched if tags ({if_starts} starts, {if_ends} ends)")
        
        # 4. Unclosed for loops
        for_starts = content.count('{% for')
        for_ends = content.count('{% endfor')
        if for_starts != for_ends:
            errors.append(f"{rel_path}: Mismatched for tags ({for_starts} starts, {for_ends} ends)")
        
        # 5. Unclosed with statements
        with_starts = content.count('{% with')
        with_ends = content.count('{% endwith')
        if with_starts != with_ends:
            errors.append(f"{rel_path}: Mismatched with tags ({with_starts} starts, {with_ends} ends)")
        
        # Try to compile template
        try:
            template = Template(content)
            # Try to render with empty context
            context = Context({})
            template.render(context)
        except TemplateSyntaxError as e:
            errors.append(f"{rel_path}: Template syntax error - {str(e)}")
            # #region agent log
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'location': 'check_templates.py:template_error',
                    'message': 'Template syntax error found',
                    'data': {'file': rel_path, 'error': str(e)},
                    'timestamp': django.utils.timezone.now().isoformat(),
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'B'
                }) + '\n')
            # #endregion
        except Exception as e:
            # Some templates might need specific context variables, that's OK
            warnings.append(f"{rel_path}: Could not render (might need context): {str(e)}")
    
    except Exception as e:
        errors.append(f"{rel_path}: Error reading file - {str(e)}")
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'location': 'check_templates.py:file_error',
                'message': 'Error reading template file',
                'data': {'file': rel_path, 'error': str(e)},
                'timestamp': django.utils.timezone.now().isoformat(),
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B'
            }) + '\n')
        # #endregion

# #region agent log
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({
        'location': 'check_templates.py:complete',
        'message': 'Template validation complete',
        'data': {'errors': len(errors), 'warnings': len(warnings), 'files_checked': len(template_files)},
        'timestamp': django.utils.timezone.now().isoformat(),
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'B'
    }) + '\n')
# #endregion

print("=" * 80)
print("TEMPLATE SYNTAX VALIDATION REPORT")
print("=" * 80)
print(f"\nTemplates checked: {len(template_files)}")
print(f"Errors found: {len(errors)}")
print(f"Warnings found: {len(warnings)}")

if errors:
    print("\n" + "=" * 80)
    print("ERRORS:")
    print("=" * 80)
    for error in errors:
        print(f"  [ERROR] {error}")

if warnings:
    print("\n" + "=" * 80)
    print("WARNINGS:")
    print("=" * 80)
    for warning in warnings:
        print(f"  [WARN] {warning}")

if not errors and not warnings:
    print("\n[OK] No errors or warnings found!")

