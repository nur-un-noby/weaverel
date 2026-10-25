from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('variant-info/<int:product_id>/', views.get_variant_info, name='get_variant_info'),
    path('track-order/', views.track_order, name='track_order'),
    path('guide/', views.guide_view, name='guide'),
    path('health/', views.health_check, name='health_check'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]
