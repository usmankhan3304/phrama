# serializers.py
from django.utils import timezone
from rest_framework import serializers
from scraper.models import *
from data_uploader.models import *


class DrugGenericNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSDrug
        fields = ['generic_name', 'ingredient', 'strength', 'dosage_form', 'route',"image_urls"]

class DrugTradeNameSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()  
    price_type = serializers.SerializerMethodField()

    class Meta:
        model = FSSDrug
        fields = ['trade_name', 'ingredient', 'price', 'package_description', 'ndc_with_dashes', "price_type"]
    
    # def get_price_type(self, obj):
    #     price_type_filter = self.context.get('price_type', None)
        
    #     if price_type_filter:
    #         pricing = obj.pricings.filter(price_type=price_type_filter).first()
    #         return pricing.price_type if pricing else None
        
    #     pricing = obj.pricings.first()
    #     return pricing.price_type if pricing else None



class DrugContractorsSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.vendor_name', allow_null=True)
    contract_number = serializers.CharField(source='contract.contract_number')
    trade_name = serializers.CharField()
    contract_start_date = serializers.DateField(format="%Y-%m-%d", source='contract.contract_start_date')
    contract_stop_date = serializers.DateField(format="%Y-%m-%d", source='contract.contract_stop_date')

    class Meta:
        model = FSSDrug
        fields = ['vendor_name', 'contract_number', 'trade_name', 'contract_start_date', 'contract_stop_date']



class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['name']

class PricingSerializer(serializers.ModelSerializer):
    price_start_date = serializers.DateField(format="%Y-%m-%d")
    price_stop_date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = FSSPricing
        fields = ['price_type', 'price', 'price_start_date', 'price_stop_date']

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSContract
        fields = ['contract_number', 'awarded_value', 'estimated_annual_quantities', 'awardee']

class DrugFullDetailSerializer(serializers.ModelSerializer):
    manufactured_by = ManufacturerSerializer()
    manufactured_for = ManufacturerSerializer()
    distributed_by = ManufacturerSerializer()
    contract = ContractSerializer()
    pricing_info = PricingSerializer(source='pricings', many=True)  # Assuming 'pricings' is the related name

    class Meta:
        model = FSSDrug
        fields = ['trade_name', 'ingredient', 'strength', 'package_description', 'ndc_with_dashes',
                  'contract', 'dosage_form', 'route', 'manufactured_by', 'manufactured_for', 'distributed_by', 'pricing_info','image_urls','notes']



class DrugDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSDrug
        fields = ['va_class', 'covered', 'prime_vendor']

class ContractDetailSerializer(serializers.ModelSerializer):
    drugs = DrugDetailSerializer(many=True, read_only=True)

    class Meta:
        model = FSSContract
        fields = ['contract_number', 'contract_start_date', 'contract_stop_date', 'drugs']

class VendorDetailSerializer(serializers.ModelSerializer):
    contracts = ContractDetailSerializer(many=True, read_only=True)

    class Meta:
        model = FSSVendor
        fields = ['vendor_name','notes', 'contracts']
        
        

class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSPricing
        fields = ['price']

class DrugDetailByVendorSerializer(serializers.ModelSerializer):
    ndc_code = serializers.CharField(source='ndc_with_dashes')
    price = serializers.SerializerMethodField()

    class Meta:
        model = FSSDrug
        fields = ['trade_name', 'ingredient', 'strength', 'ndc_code', 'price']
        


class VendorsInfoSerializer(serializers.ModelSerializer):
    contracts = ContractSerializer(many=True, read_only=True)

    class Meta:
        model = FSSVendor
        fields = ['id', 'vendor_name', 'contracts']

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSSDrug
        fields = ['generic_name', 'ingredient', 'strength', 'dosage_form', 'route']


class PotentialLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PotentialLead
        fields = ['active_ingredient','application_number', 'applicant_holder', 'te_code', 'market_status']


class AccessDrugShortageDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessDrugShortageData
        fields = '__all__'

class AsphDrugShortageDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsphDrugShortageData
        fields = '__all__'
    
    
class FOIAUniqueNDCDataSerializer(serializers.ModelSerializer):
    distributed_by = serializers.SerializerMethodField()
    manufactured_by = serializers.SerializerMethodField()
    manufactured_for = serializers.SerializerMethodField()

    class Meta:
        model = FOIAUniqueNDCData
        fields = [
            'id', 'ndc_code','description', 'total_quantity_purchased', 
            'total_publishable_dollars_spent', 'ingredient', 'dosage_form', 
            'strength', 'manufactured_by', 'manufactured_for', 'distributed_by','notes'
        ]

    def get_distributed_by(self, obj):
        return obj.distributed_by.name if obj.distributed_by else None

    def get_manufactured_by(self, obj):
        return obj.manufactured_by.name if obj.manufactured_by else None

    def get_manufactured_for(self, obj):
        return obj.manufactured_for.name if obj.manufactured_for else None


class FOIADrugsDataSerializer(serializers.ModelSerializer):
    facility_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = FOIADrugsData
        fields = [
            'mckesson_station_number', 
            'ndc_code', 
            'quantity_purchased', 
            'publishable_dollars_spent',
            'facility_name',
            'address'
        ]

    def get_facility_name(self, obj):
        try:
            station_data = FOIAStationData.objects.get(station_id=obj.mckesson_station_number)
            return station_data.facility_name
        except FOIAStationData.DoesNotExist:
            return ''

    def get_address(self, obj):
        try:
            station_data = FOIAStationData.objects.get(station_id=obj.mckesson_station_number)
            return station_data.address
        except FOIAStationData.DoesNotExist:
            return ''
        
        

class DODDrugsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DODDrugData
        fields = '__all__'      


class DrugSerializer(serializers.ModelSerializer):
    price_on_fss = serializers.SerializerMethodField()
    price_on_foia = serializers.SerializerMethodField()
    price_on_dod = serializers.SerializerMethodField()
    vendor_name = serializers.CharField(source='vendor.vendor_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    expire_in_month = serializers.SerializerMethodField()
    contract_expire_date = serializers.SerializerMethodField()
    price_type = serializers.SerializerMethodField()

    class Meta:
        model = FSSDrug
        fields = [
            'id', 'price_on_fss', 'price_on_foia', 'price_on_dod', 'vendor_name', 'contract_number',
            'ndc_with_dashes', 'trade_name', 'generic_name', 'package_description', 'dosage_form',
            'strength', 'route', 'va_class', 'covered', 'prime_vendor', 'ingredient', 'manufactured_by',
            'manufactured_for', 'distributed_by', 'days_until_expiry', 'expire_in_month','contract_expire_date', 'price_type'
        ]

    def get_price_on_fss(self, obj):
        pricing = FSSPricing.objects.filter(drug=obj).first()
        return pricing.price if pricing else None

    def get_price_on_foia(self, obj):
        ndc_code = obj.ndc_with_dashes.replace("-", "")
        foia_data = FOIAUniqueNDCData.objects.filter(ndc_code=ndc_code).first()
        return foia_data.total_publishable_dollars_spent if foia_data else None

    def get_price_on_dod(self, obj):
        ndc_code = obj.ndc_with_dashes.replace("-", "")
        dod_data = DODDrugData.objects.filter(ndc_code=ndc_code).first()
        return dod_data.price if dod_data else None
    
    def get_days_until_expiry(self, obj):
        today = timezone.now().date()
        return (obj.contract.contract_stop_date - today).days

    def get_expire_in_month(self, obj):
        days_until_expiry = self.get_days_until_expiry(obj)
        if days_until_expiry <= 30:
            return "Expire in 1 month" if days_until_expiry == 30 else "Expire in less than 1 month"
        elif days_until_expiry <= 60:
            return "Expire in 2 months" if days_until_expiry == 60 else "Expire in less than 2 months"
        elif days_until_expiry <= 90:
            return "Expire in 3 months" if days_until_expiry == 90 else "Expire in less than 3 months"
        elif days_until_expiry <= 120:
            return "Expire in 4 months" if days_until_expiry == 120 else "Expire in less than 4 months"
        elif days_until_expiry <= 150:
            return "Expire in 5 months" if days_until_expiry == 150 else "Expire in less than 5 months"
        elif days_until_expiry <= 180:
            return "Expire in 6 months" if days_until_expiry == 180 else "Expire in less than 6 months"
        elif days_until_expiry <= 210:
            return "Expire in 7 months" if days_until_expiry == 210 else "Expire in less than 7 months"
        elif days_until_expiry <= 240:
            return "Expire in 8 months" if days_until_expiry == 240 else "Expire in less than 8 months"
        elif days_until_expiry <= 270:
            return "Expire in 9 months" if days_until_expiry == 270 else "Expire in less than 9 months"
        elif days_until_expiry <= 300:
            return "Expire in 10 months" if days_until_expiry == 300 else "Expire in less than 10 months"
        elif days_until_expiry <= 330:
            return "Expire in 11 months" if days_until_expiry == 330 else "Expire in less than 11 months"
        elif days_until_expiry <= 360:
            return "Expire in 12 months" if days_until_expiry == 360 else "Expire in less than 12 months"
        else:
            return "Expire in more than 12 months"
        
    def get_contract_expire_date(self, obj):  
        return obj.contract.contract_stop_date
    
    def get_price_type(self, obj):
        # Get the price type filter from context
        price_type_filter = self.context.get('price_type', None)
        
        # If price_type_filter is provided, find the matching pricing
        if price_type_filter:
            pricing = obj.pricings.filter(price_type=price_type_filter).first()
            return pricing.price_type if pricing else None
        
        # If no filter is applied, check if any price type exists
        # Return the price type of the first pricing entry if available
        pricing = obj.pricings.first()
        return pricing.price_type if pricing else None


class ScrapingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingStatus
        fields = ['start_time', 'end_time', 'status', 'task_id']


class RelatedTradeNameSerializer(serializers.ModelSerializer):
    ndc_code = serializers.CharField(source='ndc_with_dashes')
    price_type = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
     
    estimated_annual_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True, coerce_to_string=False)
    estimated_resolicitation_date = serializers.DateField(allow_null=True, required=False)
    offers = serializers.IntegerField(allow_null=True, required=False)
    estimated_annual_spend = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True, coerce_to_string=False)



    class Meta:
        model = FSSDrug
        fields = ['id','trade_name',
                   'ndc_code', 'price_type', 'price',
                   'estimated_annual_quantity',
                   'estimated_resolicitation_date',
                  'estimated_annual_spend','offers'
                  ]

    def get_price_type(self, obj):
        
        pricing = obj.pricings.first()  
        return pricing.price_type if pricing else None

    def get_price(self, obj):
        pricing = obj.pricings.first()  
        return pricing.price if pricing else None

class FOIAMonthlyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FOIAMonthlyStats
        fields = [
            'ndc', 
            'product_name', 
            'strength', 
            'total_dollar_spent', 
            'total_units_purchased', 
            'min_purchase_price', 
            'max_purchase_price', 
            'month', 
            'year'
        ]