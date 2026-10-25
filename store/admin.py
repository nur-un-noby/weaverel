from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin controls for Categories (Panjabi, Shirts, T-Shirts, etc.).
    Admins can rename, change sort order, or hide/activate categories anytime.
    """
    list_display = ('name', 'slug', 'display_order', 'is_active', 'get_product_count')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')

    def get_product_count(self, obj):
        return obj.products.count()
    get_product_count.short_description = "Total Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin controls for clothing products with instant inline price & stock updates.
    """
    list_display = (
        'name', 
        'category', 
        'sku', 
        'price', 
        'discount_price', 
        'stock', 
        'is_available', 
        'is_featured'
    )
    list_filter = ('category', 'is_available', 'is_featured', 'created_at')
    list_editable = ('price', 'discount_price', 'stock', 'is_available', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'sku', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'description', 'fabric_details')
        }),
        ('Pricing (in BDT ৳)', {
            'fields': ('price', 'discount_price')
        }),
        ('Inventory & Sizing', {
            'fields': ('stock', 'available_sizes', 'color', 'is_available', 'is_featured', 'badge')
        }),
        ('Imagery', {
            'fields': ('image_url', 'image')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
