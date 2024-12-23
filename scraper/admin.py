from django.contrib import admin
from .models import *

@admin.register(FSSVendor)
class FSSVendorAdmin(admin.ModelAdmin):
    search_fields = ['vendor_name']
    

@admin.register(FSSContract)
class FSSContractAdmin(admin.ModelAdmin):
    search_fields = ['contract_number', 'awardee', 'vendor__vendor_name']

@admin.register(FSSDrug)
class FSSDrugAdmin(admin.ModelAdmin):
    list_display = ['generic_name', 'ndc_with_dashes', 'ingredient', 'dosage_form', 'strength','id']
    search_fields = ['strength','generic_name','ndc_with_dashes',]
    
    #search_fields = ['trade_name', 'generic_name', 'ndc_with_dashes', 'ingredient','strength']

@admin.register(FSSPricing)
class FSSPricingAdmin(admin.ModelAdmin):
    search_fields = ['drug__trade_name', 'price_type', 'non_taa_compliance']

@admin.register(PotentialLead)
class PotentialLeadAdmin(admin.ModelAdmin):
    search_fields = ['active_ingredient', 'application_number', 'applicant_holder']

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    search_fields = ['name','address']

@admin.register(AsphDrugShortageData)
class AsphDrugShortageDataAdmin(admin.ModelAdmin):
    search_fields = ['generic_name', 'shortage_status']

@admin.register(AccessDrugShortageData)
class AccessDrugShortageDataAdmin(admin.ModelAdmin):
    search_fields = ['generic_name', 'shortage_status']

@admin.register(FOIAUniqueNDCData)
class FOIAUniqueNDCDataAdmin(admin.ModelAdmin):
    search_fields = ['ndc_code', 'description', 'ingredient']

@admin.register(FOIADrugsData)
class FOIADrugsDataAdmin(admin.ModelAdmin):
    search_fields = ['ndc_code__ndc_code', 'quantity_purchased', 'publishable_dollars_spent']

@admin.register(ScrapingStatus)
class ScrapingStatusAdmin(admin.ModelAdmin):
    search_fields = ['status', 'task_id']

@admin.register(DataInsertionRecord)
class DataInsertionRecordAdmin(admin.ModelAdmin):
    search_fields = ['drug_type', 'date_inserted']

@admin.register(DODDrugData)
class DODDrugDataAdmin(admin.ModelAdmin):
    search_fields = ['ndc_code', 'description']

# For any other models, you can register them similarly.
