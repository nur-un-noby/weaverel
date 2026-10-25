from django.contrib import admin
from .models import SiteConfiguration, HeroBanner


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding & Identity', {
            'fields': ('site_name', 'site_name_bn', 'logo', 'tagline', 'tagline_bn')
        }),
        ('Announcement Bar', {
            'fields': ('announcement_active', 'announcement_text_en', 'announcement_text_bn')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'whatsapp_number', 'contact_email', 'address_en', 'address_bn')
        }),
        ('Store Policies & Delivery', {
            'fields': ('currency_symbol', 'currency_code', 'free_shipping_threshold', 'enable_cod')
        }),
        ('Social Links', {
            'fields': ('facebook_url', 'instagram_url', 'youtube_url')
        }),
        ('SEO Defaults', {
            'fields': ('meta_title', 'meta_description')
        }),
    )

    def has_add_permission(self, request):
        # Only allow 1 instance
        return SiteConfiguration.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('title_en', 'title_bn', 'badge_en', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('title_en', 'title_bn')
    ordering = ('display_order',)
