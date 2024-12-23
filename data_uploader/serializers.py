from rest_framework import serializers
from scraper.models import FSSDrug,Manufacturer

class DODUploadedFileSerializer(serializers.Serializer):
    dod_file = serializers.FileField()




class FSSDrugUpdateSerializer(serializers.Serializer):
    offers = serializers.IntegerField(required=False, allow_null=True)
    estimated_resolicitation_date = serializers.DateField(required=False, allow_null=True)
    estimated_annual_spend = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        error_messages={
            'invalid': 'Estimated annual spend must be a valid decimal number.'
        }
    )
    estimated_annual_quantity = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True,
        error_messages={
            'invalid': 'Estimated annual quantity must be a valid string.'
        }
    )

    def update(self, instance, validated_data):
        instance.offers = validated_data.get('offers', instance.offers)
        instance.estimated_annual_spend = validated_data.get('estimated_annual_spend', instance.estimated_annual_spend)
        instance.estimated_resolicitation_date = validated_data.get('estimated_resolicitation_date', instance.estimated_resolicitation_date)
        instance.save()

        estimated_annual_quantity = validated_data.get('estimated_annual_quantity')
        if estimated_annual_quantity is not None:
            contract = instance.contract
            if contract:
                contract.estimated_annual_quantities = estimated_annual_quantity
                contract.save()

        return instance




class FSSDrugNotesSerializerNotes(serializers.Serializer):
    id = serializers.IntegerField()
    notes = serializers.CharField() 


class FOIADrugNotesSerializerNotes(serializers.Serializer):
    id = serializers.IntegerField()
    notes = serializers.CharField()   


class FSSVendorNotesSerializerNotes(serializers.Serializer):
    id = serializers.IntegerField()
    notes = serializers.CharField()   



class ManufacturerUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)

    manufactured_by = serializers.CharField()
    manufactured_for = serializers.CharField()
    manufactured_address = serializers.CharField()



class FOIAMonthlyStatsFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value

