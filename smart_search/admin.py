from django.contrib import admin
from .models import ConsolidatedDrugData, ConsolidatedDrugPrice
# Register your models here.

@admin.register(ConsolidatedDrugData)
class ConsolidatedDrugDataAdmin(admin.ModelAdmin):
    list_display = ['generic_name', 'ndc_code', 'ingredient', 'dosage_form', 'strength','id']
    search_fields = ['strength','generic_name','ndc_code','ingredient']


@admin.register(ConsolidatedDrugPrice)
class ConsolidatedDrugPricedmin(admin.ModelAdmin):
    search_fields = ['drug__trade_name', 'price_type', 'non_taa_compliance']

  