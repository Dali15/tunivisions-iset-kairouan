from django import template

register = template.Library()


@register.filter
def can_access(user, permission):
	return user.can_access(permission)

# Add your custom filters here
# Example:
# @register.filter
# def custom_filter_name(value):
#     return value
