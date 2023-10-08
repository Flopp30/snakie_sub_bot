from django.contrib import admin

from product.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'is_active', 'displayed_name', 'amount', 'currency', 'sub_period', 'sub_period_type', 'is_trial'
    )
    ordering = ('-id', '-is_active', 'displayed_name')
    list_per_page = 20
    list_filter = (
        'currency',
        'is_trial',
    )
    search_fields = ('displayed_name', 'amount', 'currency')
