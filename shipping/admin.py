from django.contrib import admin
from .models import ShippingZone


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_bn', 'charge', 'estimated_delivery_en', 'free_delivery_allowed', 'is_active', 'display_order')
    list_editable = ('charge', 'free_delivery_allowed', 'is_active', 'display_order')
    search_fields = ('code', 'name_en', 'name_bn')
    ordering = ('display_order',)
