from django import template

register = template.Library()

@register.simple_tag
def get_color_classes(color):
    """Get color classes based on color name"""
    colors = {
        'blue': {
            'text_color': 'text-blue-600',
            'bg_color': 'bg-blue-600',
            'hover_bg': 'hover:bg-blue-700',
            'ring_color': 'ring-blue-500',
            'bg_light': 'bg-blue-50',
            'border_color': 'border-blue-200',
            'text_dark': 'text-blue-900',
        },
        'purple': {
            'text_color': 'text-purple-600',
            'bg_color': 'bg-purple-600',
            'hover_bg': 'hover:bg-purple-700',
            'ring_color': 'ring-purple-500',
            'bg_light': 'bg-purple-50',
            'border_color': 'border-purple-200',
            'text_dark': 'text-purple-900',
        },
        'green': {
            'text_color': 'text-green-600',
            'bg_color': 'bg-green-600',
            'hover_bg': 'hover:bg-green-700',
            'ring_color': 'ring-green-500',
            'bg_light': 'bg-green-50',
            'border_color': 'border-green-200',
            'text_dark': 'text-green-900',
        },
        'red': {
            'text_color': 'text-red-600',
            'bg_color': 'bg-red-600',
            'hover_bg': 'hover:bg-red-700',
            'ring_color': 'ring-red-500',
            'bg_light': 'bg-red-50',
            'border_color': 'border-red-200',
            'text_dark': 'text-red-900',
        },
        'indigo': {
            'text_color': 'text-indigo-600',
            'bg_color': 'bg-indigo-600',
            'hover_bg': 'hover:bg-indigo-700',
            'ring_color': 'ring-indigo-500',
            'bg_light': 'bg-indigo-50',
            'border_color': 'border-indigo-200',
            'text_dark': 'text-indigo-900',
        },
        'yellow': {
            'text_color': 'text-yellow-600',
            'bg_color': 'bg-yellow-600',
            'hover_bg': 'hover:bg-yellow-700',
            'ring_color': 'ring-yellow-500',
            'bg_light': 'bg-yellow-50',
            'border_color': 'border-yellow-200',
            'text_dark': 'text-yellow-900',
        },
        'pink': {
            'text_color': 'text-pink-600',
            'bg_color': 'bg-pink-600',
            'hover_bg': 'hover:bg-pink-700',
            'ring_color': 'ring-pink-500',
            'bg_light': 'bg-pink-50',
            'border_color': 'border-pink-200',
            'text_dark': 'text-pink-900',
        },
    }
    return colors.get(color, colors['indigo'])

