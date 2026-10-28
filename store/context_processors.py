from .models import Category
from shipping.districts import BANGLADESH_DIVISIONS, BANGLADESH_DISTRICT_CHOICES


def store_context(request):
    """
    Exposes active categories and Bangladesh 64 districts globally to every template.
    Admin changes (add/rename/delete/reorder) instantly reflect site-wide.
    """
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    return {
        'all_categories': categories,
        'bangladesh_divisions': BANGLADESH_DIVISIONS,
        'bangladesh_districts': BANGLADESH_DISTRICT_CHOICES,
    }
