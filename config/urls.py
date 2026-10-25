"""
Main URL Configuration for Weaverel Clothing project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from store_settings.views import admin_analytics_view

urlpatterns = [
    path('admin/analytics/', admin_analytics_view, name='admin_analytics'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Standard Django language switcher
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('wishlist/', include('wishlist.urls', namespace='wishlist')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('', include('store.urls', namespace='store')),
]

# Custom Error Handlers
handler404 = 'store.views.custom_404'
handler500 = 'store.views.custom_500'

# Serve media and static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
