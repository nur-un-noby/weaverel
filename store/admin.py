from django.contrib import admin
from .models import Category, Size, Color, Product, ProductVariant, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_url', 'alt_text', 'display_order')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'color', 'sku', 'price_override', 'stock', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_bn', 'slug', 'parent',
                    'display_order', 'is_active', 'get_product_count')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'name_bn', 'description')
    ordering = ('display_order', 'name')

    def get_product_count(self, obj):
        return obj.products.count()
    get_product_count.short_description = "Products"


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order')
    list_editable = ('display_order',)
    search_fields = ('name',)
    ordering = ('display_order', 'name')


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_bn', 'hex_code')
    search_fields = ('name', 'name_bn')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'display_order',
        'name',
        'category',
        'sku',
        'price',
        'discount_price',
        'get_total_stock',
        'is_available',
        'is_featured',
        'is_new_arrival',
    )
    list_filter = ('category', 'is_available', 'is_featured',
                   'is_new_arrival', 'created_at')
    list_display_links = ('name',)
    list_editable = ('display_order', 'price', 'discount_price', 'is_available', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'name_bn', 'sku', 'description')
    ordering = ('display_order', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductVariantInline, ProductImageInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_bn', 'slug', 'sku', 'category', 'description', 'description_bn', 'fabric_details', 'fabric_details_bn')
        }),
        ('Pricing (in BDT ৳)', {
            'fields': ('price', 'discount_price')
        }),
        ('Display & Flags (Page Positioning)', {
            'fields': ('display_order', 'badge', 'is_featured', 'is_new_arrival', 'is_available')
        }),
        ('Primary Imagery', {
            'fields': ('image', 'image_url')
        }),
        ('Inventory & Sizing', {
            'fields': ('stock', 'available_sizes', 'color'),
            'classes': ('collapse',)
        }),
        ('SEO Metadata', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Audit Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_total_stock(self, obj):
        return obj.total_stock
    get_total_stock.short_description = "Stock"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'size', 'color',
                    'price_override', 'stock', 'is_active')
    list_filter = ('is_active', 'size', 'color')
    list_editable = ('stock', 'is_active')
    search_fields = ('sku', 'product__name')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'display_order', 'alt_text')
    list_editable = ('display_order',)
