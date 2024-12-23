import django_filters
from scraper.models import FSSDrug, FOIAUniqueNDCData, FOIADrugsData, FOIAStationData, DODDrugData, PotentialLead, AccessDrugShortageData, AsphDrugShortageData

class FSSDrugFilter(django_filters.FilterSet):
    class Meta:
        model = FSSDrug
        fields = {
            'trade_name': ['icontains'],
            'generic_name': ['icontains'],
            'ingredient': ['icontains'],
            'strength': ['icontains'],
        }

class FOIAUniqueNDCDataFilter(django_filters.FilterSet):
    class Meta:
        model = FOIAUniqueNDCData
        fields = {
            'description': ['icontains'],
            'ingredient': ['icontains'],
            'dosage_form': ['icontains'],
            'strength': ['icontains'],
        }

class FOIADrugsDataFilter(django_filters.FilterSet):
    class Meta:
        model = FOIADrugsData
        fields = {
            'mckesson_station_number': ['icontains'],
            'quantity_purchased': ['exact', 'gte', 'lte'],
        }

class FOIAStationDataFilter(django_filters.FilterSet):
    class Meta:
        model = FOIAStationData
        fields = {
            'facility_name': ['icontains'],
            'state': ['exact'],
        }

class DODDrugDataFilter(django_filters.FilterSet):
    class Meta:
        model = DODDrugData
        fields = {
            'description': ['icontains'],
            'price': ['exact', 'gte', 'lte'],
            'quantity': ['exact', 'gte', 'lte'],
        }

class PotentialLeadFilter(django_filters.FilterSet):
    class Meta:
        model = PotentialLead
        fields = {
            'active_ingredient': ['icontains'],
            'application_number': ['icontains'],
            'market_status': ['icontains'],
            'dosage_form': ['icontains'],
            'strength': ['icontains'],
        }

class AccessDrugShortageDataFilter(django_filters.FilterSet):
    class Meta:
        model = AccessDrugShortageData
        fields = {
            'generic_name': ['icontains'],
            'shortage_status': ['icontains'],
        }

class AsphDrugShortageDataFilter(django_filters.FilterSet):
    class Meta:
        model = AsphDrugShortageData
        fields = {
            'generic_name': ['icontains'],
            'shortage_status': ['icontains'],
        }
