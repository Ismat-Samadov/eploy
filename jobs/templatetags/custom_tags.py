# # jobs/templatetags/custom_tags.py

# from django import template

# register = template.Library()

# @register.filter(name='add_class')
# def add_class(value, css_class):
#     return value.as_widget(attrs={'class': css_class})

from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    try:
        return field.as_widget(attrs={"class": css_class})
    except AttributeError:
        # Log the error or handle it as needed
        return field  # or raise an error if this is not expected

