from django import template

register = template.Library()

print("Custom filters loaded!")  # Add this line for debugging

@register.filter
def get_range(value):
    return range(1, value + 1)

@register.filter(name='custom_filter')
def custom_filter(value):
    return value.upper()
