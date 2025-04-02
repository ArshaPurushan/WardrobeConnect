from django import template

register = template.Library()

@register.filter
def get_item(sizes, size_value):
    """Retrieve the stock for a specific size."""
    for size in sizes.all():
        if size.size == size_value:
            return size.stock  # Return only the stock
    return 0  # Return 0 if no size is found