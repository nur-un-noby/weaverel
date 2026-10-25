from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google/login/', views.google_login_view, name='google_login'),
    path('google/login/callback/', views.google_callback_view, name='google_callback'),
    path('google/callback/', views.google_callback_view, name='google_callback_legacy'),
    path('google/auto-login/', views.google_auto_login_view, name='google_auto_login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.address_add_view, name='address_add'),
    path('addresses/<int:address_id>/edit/', views.address_edit_view, name='address_edit'),
    path('addresses/<int:address_id>/delete/', views.address_delete_view, name='address_delete'),
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.order_cancel_view, name='order_cancel'),
]
