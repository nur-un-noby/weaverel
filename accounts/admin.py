from django.contrib import admin
from .models import CustomerProfile, Address


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'district', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number', 'district')
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'title', 'recipient_name', 'phone_number', 'district', 'is_default')
    list_filter = ('district', 'is_default')
    search_fields = ('recipient_name', 'phone_number', 'address_line')
