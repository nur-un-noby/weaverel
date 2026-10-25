from .models import Category


def store_context(request):
    """
    Exposes active categories globally to every template.
    Admin changes (add/rename/delete/reorder) instantly reflect site-wide.
    """
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    return {
        'all_categories': categories,
    }
