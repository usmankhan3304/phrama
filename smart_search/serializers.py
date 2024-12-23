from rest_framework import serializers
from scraper.models import *
from .filters_fields import *
from .models import *


class FSSDrugSerializer(serializers.ModelSerializer):
    contract = serializers.CharField(source='contract.contract_number')
    vendor = serializers.CharField(source='vendor.vendor_name')
    manufactured_by = serializers.CharField(source='manufactured_by.name', allow_null=True)
    manufactured_for = serializers.CharField(source='manufactured_for.name', allow_null=True)
    distributed_by = serializers.CharField(source='distributed_by.name', allow_null=True)
    
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source='pricings__price', required=False)
    price_start_date = serializers.DateField(source='pricings__price_start_date', required=False)
    price_stop_date = serializers.DateField(source='pricings__price_stop_date', required=False)
    price_type = serializers.CharField(source='pricings__price_type', required=False)
    non_taa_compliance = serializers.CharField(source='pricings__non_taa_compliance', required=False)

    class Meta:
        model = FSSDrug
        fields = [
            'id', 'ndc_with_dashes', 'trade_name', 'generic_name', 
            'package_description', 'dosage_form', 'strength', 'route',
            'va_class', 'covered', 'prime_vendor', 'ingredient', 
            'image_urls', 'estimated_resolicitation_date', 
            'offers', 'estimated_annual_spend', 'notes', 
            'contract', 'vendor', 'manufactured_by', 
            'manufactured_for', 'distributed_by',
            'price', 'price_start_date', 'price_stop_date', 'price_type', 'non_taa_compliance'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Retrieve requested columns from context
        requested_fields = self.context.get('requested_fields', [])
        
        include_pricing = (
            not requested_fields or 
            any(field in requested_fields for field in ['Price', 'Price Start Date', 'Price Stop Date', 'Price Type', 'Non-TAA Compliance'])
        )

        # Add related pricing fields if requested
        if include_pricing:
            latest_pricing = instance.pricings.order_by('-price_start_date').first()
            representation['price'] = latest_pricing.price if latest_pricing else None
            representation['price_start_date'] = latest_pricing.price_start_date if latest_pricing else None
            representation['price_stop_date'] = latest_pricing.price_stop_date if latest_pricing else None
            representation['price_type'] = latest_pricing.price_type if latest_pricing else None
            representation['non_taa_compliance'] = latest_pricing.non_taa_compliance if latest_pricing else None

        return representation


class ConsolidatedDrugSerializer(serializers.ModelSerializer):
    # Assuming these fields are ForeignKeys in ConsolidatedDrugData model
    vendor_name = serializers.CharField(allow_null=True, required=False)
    manufactured_by = serializers.CharField( allow_null=True, required=False)
    manufactured_for = serializers.CharField(allow_null=True, required=False)
    distributed_by = serializers.CharField( allow_null=True, required=False)

    # Pricing fields, populated from the latest ConsolidatedDrugPrice record
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_start_date = serializers.DateField(required=False)
    price_stop_date = serializers.DateField(required=False)
    price_type = serializers.CharField(required=False)
    non_taa_compliance = serializers.CharField(required=False)

    class Meta:
        model = ConsolidatedDrugData
        fields = [
            'id', 'ndc_code', 'trade_name', 'generic_name', 
            'package_description', 'dosage_form', 'strength', 'route', 
            'ingredient', 'contract_number', 'vendor_name', 'manufactured_by', 
            'manufactured_for', 'distributed_by', 'notes', 'source',
            'price', 'price_start_date', 'price_stop_date', 
            'price_type', 'non_taa_compliance'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Retrieve requested columns from context
        requested_fields = self.context.get('requested_fields', [])
        
        include_pricing = (
            not requested_fields or 
            any(field in requested_fields for field in ['Price', 'Price Start Date', 'Price Stop Date', 'Price Type', 'Non-TAA Compliance'])
        )

        # Add related pricing fields if requested
        if include_pricing:
            latest_pricing = ConsolidatedDrugPrice.objects.filter(drug=instance).order_by('-price_start_date').first()
            representation['price'] = latest_pricing.price if latest_pricing else None
            representation['price_start_date'] = latest_pricing.price_start_date if latest_pricing else None
            representation['price_stop_date'] = latest_pricing.price_stop_date if latest_pricing else None
            representation['price_type'] = latest_pricing.price_type if latest_pricing else None
            representation['non_taa_compliance'] = latest_pricing.non_taa_compliance if latest_pricing else None

        return representation
    
    
class FSSPricingSerializer(serializers.ModelSerializer):
    # Flattened fields from FSSDrug
    id = serializers.IntegerField(source='drug.id')
    ndc_with_dashes = serializers.CharField(source='drug.ndc_with_dashes')
    trade_name = serializers.CharField(source='drug.trade_name')
    generic_name = serializers.CharField(source='drug.generic_name')
    package_description = serializers.CharField(source='drug.package_description')
    dosage_form = serializers.CharField(source='drug.dosage_form')
    strength = serializers.CharField(source='drug.strength')
    route = serializers.CharField(source='drug.route')
    va_class = serializers.CharField(source='drug.va_class')
    covered = serializers.BooleanField(source='drug.covered')
    prime_vendor = serializers.BooleanField(source='drug.prime_vendor')
    ingredient = serializers.CharField(source='drug.ingredient')
    image_urls = serializers.JSONField(source='drug.image_urls')
    estimated_resolicitation_date = serializers.DateField(source='drug.estimated_resolicitation_date', allow_null=True)
    offers = serializers.IntegerField(source='drug.offers', allow_null=True)
    estimated_annual_spend = serializers.DecimalField(source='drug.estimated_annual_spend', max_digits=15, decimal_places=2, allow_null=True)
    notes = serializers.CharField(source='drug.notes', allow_null=True)

    # Foreign key fields with related names
    contract = serializers.CharField(source='drug.contract.contract_number')
    vendor = serializers.CharField(source='drug.vendor.vendor_name')
    manufactured_by = serializers.CharField(source='drug.manufactured_by.name', allow_null=True)
    manufactured_for = serializers.CharField(source='drug.manufactured_for.name', allow_null=True)
    distributed_by = serializers.CharField(source='drug.distributed_by.name', allow_null=True)

    class Meta:
        model = FSSPricing
        fields = [
            'id', 'ndc_with_dashes', 'trade_name', 'generic_name', 
            'package_description', 'dosage_form', 'strength', 'route',
            'va_class', 'covered', 'prime_vendor', 'ingredient', 
            'image_urls', 'estimated_resolicitation_date', 
            'offers', 'estimated_annual_spend', 'notes', 
            'contract', 'vendor', 'manufactured_by', 'manufactured_for', 'distributed_by',
            'price', 'price_start_date', 'price_stop_date', 'price_type', 'non_taa_compliance'
        ]

class FSSContractSerializer(serializers.ModelSerializer):
    vendor = serializers.CharField(source='vendor.vendor_name')

    class Meta:
        model = FSSContract
        fields = ['contract_number', 'awardee', 'awarded_value', 'estimated_annual_quantities', 'contract_start_date', 'contract_stop_date', 'vendor']

class FSSVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSVendor
        fields = ['vendor_name']

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['name', 'address']

class FOIAUniqueNDCDataSerializer(serializers.ModelSerializer):
    manufactured_by = serializers.CharField(source='manufactured_by.name', allow_null=True)
    manufactured_for = serializers.CharField(source='manufactured_for.name', allow_null=True)
    distributed_by = serializers.CharField(source='distributed_by.name', allow_null=True)

    class Meta:
        model = FOIAUniqueNDCData
        fields = [
            'ndc_code', 'description', 'total_quantity_purchased', 
            'total_publishable_dollars_spent', 'ingredient', 
            'dosage_form', 'strength', 'manufactured_by', 
            'manufactured_for', 'distributed_by'
        ]

class FOIADrugsDataSerializer(serializers.ModelSerializer):
    # Flattened fields from FOIAUniqueNDCData
    ndc_code = serializers.CharField(source='ndc_code.ndc_code')
    description = serializers.CharField(source='ndc_code.description')
    ingredient = serializers.CharField(source='ndc_code.ingredient', allow_null=True)
    dosage_form = serializers.CharField(source='ndc_code.dosage_form', allow_null=True)
    strength = serializers.CharField(source='ndc_code.strength', allow_null=True)
    manufactured_by = serializers.CharField(source='ndc_code.manufactured_by.name', allow_null=True)
    manufactured_for = serializers.CharField(source='ndc_code.manufactured_for.name', allow_null=True)
    distributed_by = serializers.CharField(source='ndc_code.distributed_by.name', allow_null=True)

    class Meta:
        model = FOIADrugsData
        fields = [
            'mckesson_station_number', 'ndc_code', 'description', 'ingredient', 
            'dosage_form', 'strength', 'manufactured_by', 'manufactured_for', 
            'distributed_by', 'quantity_purchased', 'publishable_dollars_spent'
        ]

class FOIAStationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FOIAStationData
        fields = ['station_id', 'facility_name', 'address', 'state', 'phone']

class DODDrugDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DODDrugData
        fields = ['ndc_code', 'description', 'price', 'quantity']

class PotentialLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PotentialLead
        fields = [
            'active_ingredient', 'application_number', 'applicant_holder', 
            'te_code', 'market_status', 'dosage_form', 'route', 'strength'
        ]

class AccessDrugShortageDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessDrugShortageData
        fields = '__all__'

class AsphDrugShortageDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsphDrugShortageData
        fields = '__all__'
        



class FilterSerializer(serializers.Serializer):
    field = serializers.CharField()
    condition = serializers.CharField()
    value = serializers.CharField()

    def validate_field(self, value):
        return value

    def validate_condition(self, value):
        return value

class FSSDrugSearchInputSerializer(serializers.Serializer):
    filters = serializers.ListField(
        child=FilterSerializer(),
        allow_empty=False,
        help_text="List of filters to apply. Each filter must contain a 'field', 'condition', and 'value'."
    )
    columns = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of columns to include in the response. If not provided, all columns are returned."
    )