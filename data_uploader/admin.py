# admin.py
from django.contrib import admin
from .models import FOIAMonthlyStats

# Step 2: Register the Model in Admin
@admin.register(FOIAMonthlyStats)
class FOIAMonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ('ndc', 'product_name', 'strength', 'total_dollar_spent', 'total_units_purchased', 'min_purchase_price', 'max_purchase_price', 'month', 'year')
    search_fields = ('ndc', 'product_name')
    list_filter = ('month', 'year')
