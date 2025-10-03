from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Получение атрибута объекта по имени"""
    return getattr(obj, attr, '')

@register.filter
def get_field_value(obj, field_name):
    """Безопасное получение значения поля объекта"""
    if hasattr(obj, field_name):
        value = getattr(obj, field_name)
        if value is None:
            return ''
        return str(value)
    return ''

@register.filter
def field_type(obj, field_name):
    """Получение типа поля"""
    if hasattr(obj, field_name):
        return type(getattr(obj, field_name)).__name__
    return ''