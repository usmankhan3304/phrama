from django.db import models

class FSSVendor(models.Model):
    vendor_name = models.CharField(max_length=500)
    notes = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.vendor_name

class FSSContract(models.Model):
    contract_number = models.CharField(max_length=50, unique=True)  
    awardee = models.CharField(max_length=255, blank=True, null=True)
    awarded_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estimated_annual_quantities = models.CharField(max_length=255, blank=True, null=True) 
    contract_start_date = models.DateField()
    contract_stop_date = models.DateField()
    vendor = models.ForeignKey(FSSVendor, on_delete=models.CASCADE, related_name='contracts')

    def __str__(self):
        return self.contract_number

class Manufacturer(models.Model):
    name=models.CharField(max_length=500)
    address=models.CharField(max_length=500,blank=True, null=True)

    def __str__(self):
        return self.name

class FSSDrug(models.Model):
    contract = models.ForeignKey(FSSContract, on_delete=models.CASCADE, related_name='drugs')
    vendor = models.ForeignKey(FSSVendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='drugs')
    ndc_with_dashes = models.CharField(max_length=50) 
    trade_name = models.CharField(max_length=500)
    generic_name = models.CharField(max_length=500, blank=True,  null=True)
    package_description = models.CharField(max_length=500, blank=True, null=True)
    
    dosage_form = models.CharField(max_length=200)
    strength = models.CharField(max_length=200)
    route = models.CharField(max_length=200)
    va_class = models.CharField(max_length=255)
    
    covered = models.BooleanField()
    prime_vendor = models.BooleanField()
    ingredient = models.CharField(max_length=300)
    manufactured_by = models.ForeignKey(Manufacturer, related_name='manufactured_by', on_delete=models.SET_NULL, null=True, blank=True)
    manufactured_for = models.ForeignKey(Manufacturer, related_name='manufactured_for', on_delete=models.SET_NULL, null=True, blank=True)
    distributed_by = models.ForeignKey(Manufacturer, related_name='distributed_by', on_delete=models.SET_NULL, null=True, blank=True)

    
    image_urls = models.JSONField(default=list, blank=True, null=True)
    
    
    estimated_resolicitation_date = models.DateField(null=True, blank=True)  
    offers=models.IntegerField(null=True,blank=True)
    estimated_annual_spend = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # New field
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.trade_name

class FSSPricing(models.Model):
    drug = models.ForeignKey(FSSDrug, on_delete=models.CASCADE, related_name='pricings')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_start_date = models.DateField()
    price_stop_date = models.DateField()
    price_type = models.CharField(max_length=100)
    non_taa_compliance = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.drug.trade_name} - ${self.price}"

class PotentialLead(models.Model):
   
    active_ingredient = models.CharField(max_length=300)
    application_number = models.CharField(max_length=100, blank=True, null=True)
    applicant_holder = models.CharField(max_length=255)
    te_code = models.CharField(max_length=80, blank=True, null=True)
    market_status = models.CharField(max_length=100)
    dosage_form = models.CharField(max_length=300, blank=True, null=True)
    route = models.CharField(max_length=300, blank=True, null=True)
    strength = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.active_ingredient



class AccessDrugShortageData(models.Model):
    generic_name = models.CharField(max_length=500, blank=True,  null=True)
    shortage_status = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.generic_name} - {self.shortage_status}"


class AsphDrugShortageData(models.Model):
    generic_name = models.CharField(max_length=255)
    shortage_status = models.CharField(max_length=255,null=True, blank=True)
    revision_date = models.DateField()
    created_date = models.DateField()

    def __str__(self):
        return f"{self.generic_name} - Revision: {self.revision_date}, Created: {self.created_date}"



class FOIAUniqueNDCData(models.Model):
    ndc_code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255)
    total_quantity_purchased = models.IntegerField(default=0)
    total_publishable_dollars_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    ingredient = models.CharField(max_length=255, blank=True, null=True)
    dosage_form = models.CharField(max_length=255, blank=True, null=True)
    strength = models.CharField(max_length=255, blank=True, null=True)
    manufactured_by = models.ForeignKey(Manufacturer, related_name='fioa_manufactured_by', on_delete=models.SET_NULL, null=True, blank=True)
    manufactured_for = models.ForeignKey(Manufacturer, related_name='fioa_manufactured_for', on_delete=models.SET_NULL, null=True, blank=True)
    distributed_by = models.ForeignKey(Manufacturer, related_name='fioa_distributed_by', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return f"{self.ndc_code} - {self.description}"

    class Meta:
        verbose_name = "FIOA Unique NDC Data"
        verbose_name_plural = "FIOA Unique NDC Data"


class FOIADrugsData(models.Model):
    mckesson_station_number = models.CharField(max_length=20)
    ndc_code = models.ForeignKey(FOIAUniqueNDCData, on_delete=models.CASCADE, related_name='purchase_records',null=True, blank=True)
    quantity_purchased = models.IntegerField()
    publishable_dollars_spent = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.ndc_code} - {self.quantity_purchased} - {self.publishable_dollars_spent}"
    
    class Meta:
        verbose_name = "FOIA Drugs Data"
        verbose_name_plural = "FOIA Drugs Data"


class FOIAStationData(models.Model):
    station_id = models.CharField(max_length=20, unique=True)
    facility_name = models.CharField(max_length=255)
    address = models.TextField()
    state = models.CharField(max_length=5)
    phone = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.facility_name} - {self.station_id}"




class DODDrugData(models.Model):
    ndc_code = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self):
        return self.description
    


class ScrapingStatus(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Scraping started at {self.start_time} with status {self.status}"


class DataInsertionRecord(models.Model):
    DRUG_TYPE_CHOICES = [
        ('FSS', 'FSS'),
        ('FOIA', 'FOIA'),
        ('DOD', 'DOD'),
    ]

    drug_type = models.CharField(max_length=10, choices=DRUG_TYPE_CHOICES)
    date_inserted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drug_type} data inserted on {self.date_inserted}"