from django.contrib import admin
from .models import ProductReview


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer_name', 'customer_location', 'rating', 'is_verified_buyer', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_buyer', 'is_approved', 'customer_location', 'created_at')
    list_editable = ('is_approved', 'is_verified_buyer')
    search_fields = ('customer_name', 'customer_location', 'title', 'comment', 'product__name')
