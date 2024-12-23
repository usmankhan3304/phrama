# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


urlpatterns = [
    
    path('drugs-by-generic/', DrugByGenericViewSet.as_view({"get": "drugs_by_generic_name"}), name="drugs_by_generic_name"),
    path('drugs/generic/export/', DrugByGenericViewSet.as_view({"get": "export_to_excel"}), name="drugs_generic_export"),  # Export API
    
    path('drugs-by-trade/', DrugByTradeViewSet.as_view({"get": "drug_by_trade_name"}), name="drugs_by_trade_name"),
    path('drugs/trade/export/', DrugByTradeViewSet.as_view({"get": "export_to_excel"}), name="drugs_trade_export"), # Export API
    
    path('drugs/<int:drug_id>/contractors/', DrugContractorsViewSet.as_view({"get": "drug_contractors"}), name="drug_contractors"),
    path('drugs/<int:drug_id>/details/', DrugFullDetailViewSet.as_view({"post": "details"}), name="drug_details"),
    path('drugs/related/trade-names/', RelatedTradeNamesViewSet.as_view({'get': 'related_trade_names'}), name='related_trade_names'),
    
    # path('drugs/<int:drug_id>/potential-leads/', PotentialLeadViewSet.as_view({"get": "retrieve"}), name="drug_potential_leads"),
    path('drugs/<int:drug_id>/potential-leads/', PotentialLeadViewSet.as_view({"get": "retrieve_leads"}), name="drug_potential_leads"),

    path('drugs/by-duration/', DrugsByDurationView.as_view({"get": "list"}), name='drugs_by_duration'),
    path('drugs/duration/export/', DrugsByDurationView.as_view({"get": "export_to_excel"}), name='drugs_by_duration_export'), # Export API

    path('vendors/', VendorsInfoViewSet.as_view({"get": "vendors_info"}), name="vendors"),
    path('vendors/export/', VendorsInfoViewSet.as_view({"get": "export_to_excel"}), name="vendors_export"), # Export API
    path('vendors/<int:vendor_id>/details/', VendorDetailsViewSet.as_view({"get": "vendor_details"}), name="vendor_details"),
    path('vendors/<int:vendor_id>/drugs/', DrugDetailByVendorViewSet.as_view({"get": "drugs_by_vendor"}), name="vendor_drugs"),

    path('foia/drug-records/', FIOADrugsDataViewSet.as_view({"get": "list"}), name="foia_drug_records"),
    path('foia/drugs/by-ndc-code/', FIOADrugsDataByNdcViewSet.as_view({"get": "find_by_ndc_code"}), name="foia_drug_by_ndc_code"),
    path('foia/unique-records/', FIOAUniqueNDCViewSet.as_view({"get": "list"}), name="foia_unique_records"),
    path('foia/unique/records/export/', FIOAUniqueNDCViewSet.as_view({"get": "export_to_excel"}), name="foia_unique_records"), # Export API
    path('foia/monthly-stats/', FOIAMonthlyStatsListView.as_view({"get": "get"}), name='get-foia-stats'),
    path('foia/monthly-stats/export/', FOIAMonthlyStatsListView.as_view({"get": "export_to_excel"}), name="foia-monthly-stats-export"), # Export API
    
    path('foia/unique-records/<int:pk>/details/', FIOAUniqueNDCViewSet.as_view({"get": "retrieve_by_id"}), name="foia_unique_records_by_idS"),

    path('asph/drug-shortages/', AsphDrugShortageDataViewSet.as_view({"get": "list"}), name="asph_drug_shortages"),
    path('asph/drug/shortages/export/', AsphDrugShortageDataViewSet.as_view({"get": "export_to_excel"}), name="asph_drug_shortages_export"), # Export API
    
    path('access/drug-shortages/', AccessDrugShortageDataViewSet.as_view({"get": "list"}), name="access_drug_shortages"),
    path('access/drug/shortages/export/', AccessDrugShortageDataViewSet.as_view({"get": "export_to_excel"}), name="access_drug_shortages_export"), # Export API

    path('dod/drugs-data/', DODDrugDataViewSet.as_view({"get": "list"}), name="dod_drugs_data"),
    path('dod/drugs/export/', DODDrugDataViewSet.as_view({"get": "export_to_excel"}), name="dod_drugs_data_export"), # Export API
    
    path('scraping/status/', LatestScrapingStatusView.as_view(), name='latest_scraping_status'),
    path('dashboard-data/', DashboardDataView.as_view(), name='dashboard-data'),
    
]