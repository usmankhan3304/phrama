from django.db import models

# Create your models here.


from django.db import models

class ConsolidatedDrugData(models.Model):
    ndc_code = models.CharField(max_length=100)
    trade_name = models.CharField(max_length=500, blank=True, null=True)
    generic_name = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    package_description = models.CharField(max_length=500, blank=True, null=True)
    dosage_form = models.CharField(max_length=255, blank=True, null=True)
    strength = models.CharField(max_length=255, blank=True, null=True)
    route = models.CharField(max_length=200, blank=True, null=True)
    covered = models.BooleanField(blank=True, null=True)
    prime_vendor = models.BooleanField(blank=True, null=True)
    va_class = models.CharField(max_length=255,null=True, blank=True)
    
    ingredient = models.CharField(max_length=300, blank=True, null=True)
    quantity = models.IntegerField(null=True, blank=True)
    total_quantity_purchased = models.IntegerField(default=0, null=True, blank=True)
    total_publishable_dollars_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, null=True, blank=True)
    
    vendor_name = models.CharField(max_length=500, blank=True, null=True)
    contract_number = models.CharField(max_length=100, blank=True, null=True)
    contract_awardee = models.CharField(max_length=100, blank=True, null=True)
    contract_awarded_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    contract_estimated_annual_quantities = models.CharField(max_length=255, blank=True, null=True) 
    contract_start_date = models.DateField(blank=True, null=True)
    contract_stop_date = models.DateField(blank=True, null=True)
    
   
    manufactured_by = models.CharField(max_length=500, blank=True, null=True)
    manufactured_by_address = models.CharField(max_length=500, blank=True, null=True)
    manufactured_for = models.CharField(max_length=500, blank=True, null=True)
    distributed_by = models.CharField(max_length=500, blank=True, null=True)

    source = models.CharField(max_length=50) 
    notes = models.TextField(null=True, blank=True)
    
    
    # New fields for FSS, NC, and BIG4 prices
    min_fss_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_fss_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_nc_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_nc_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_big4_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_big4_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.ndc_code} - {self.description or self.trade_name or 'No Description'}"

class ConsolidatedDrugPrice(models.Model):
    drug = models.ForeignKey(ConsolidatedDrugData, related_name='prices', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_start_date = models.DateField(blank=True, null=True)
    price_stop_date = models.DateField(blank=True, null=True)
    price_type = models.CharField(max_length=100,blank=True, null=True)
    non_taa_compliance = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.drug.ndc_code} - {self.price}"
