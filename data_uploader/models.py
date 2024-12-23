
from django.db import models
from decimal import Decimal

class FOIAMonthlyStats(models.Model):
    ndc = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255,null=True, blank=True)
    strength = models.CharField(max_length=50,null=True, blank=True)
    total_dollar_spent = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)
    total_units_purchased = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)
    min_purchase_price = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)
    max_purchase_price = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)
    month = models.CharField(max_length=20, null=True, blank=True)  # Allow null/blank for month
    year = models.PositiveIntegerField(null=True, blank=True)       # Allow null/blank for year

    def __str__(self):
        return f"{self.ndc} - {self.product_name} ({self.month}, {self.year})"
