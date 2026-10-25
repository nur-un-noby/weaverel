from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('drawer/', views.cart_drawer, name='cart_drawer'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-confirmed/<str:order_number>/', views.order_success_view, name='order_success'),
]
