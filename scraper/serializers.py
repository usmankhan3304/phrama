# serializers.py
from rest_framework import serializers
from .models import *

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSVendor
        fields = ['id', 'vendor_name']

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSContract
        fields = ['id', 'contract_number', 'awardee', 'awarded_value', 'estimated_annual_quantities', 
                  'contract_start_date', 'contract_stop_date', 'vendor']

class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSDrug
        fields = ['id', 'contract', 'vendor', 'ndc_with_dashes', 'trade_name', 'generic_name', 'dosage_form', 
                  'strength', 'route', 'va_class', 'covered', 'prime_vendor', 'ingredient', 
                  'manufactured_by', 'manufactured_for', 'distributed_by']

class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSPricing
        fields = ['id', 'drug', 'price', 'price_start_date', 'price_stop_date', 'price_type', 'non_taa_compliance']

class PotentialLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PotentialLead
        fields = ['id', 'drug', 'active_ingredient', 'applicant_holder', 'te_code', 'market_status']
        

# class NDCDrugDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FIOAPurchaseRecords
#         fields = ['ndc_code', 'description', 'total_quantity_purchased', 'total_publishable_dollars_spent']

# class FIOADrugsDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FIOADrugsData
#         fields = ['mckesson_station_number', 'ndc_code', 'quantity_purchased', 'publishable_dollars_spent']



