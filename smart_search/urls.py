from django.urls import path
from .views import AdvancedSearchView, GetColumnsView, FSSDrugSearchAPIView,PopulateConsolidatedTableView,ConsolidatedDrugSearchAPIView

urlpatterns = [
    #path('advanced/', AdvancedSearchView.as_view(), name='advanced_search'),
    #path('columns/by-source/', GetColumnsView.as_view(), name='get_columns_by_source'),
    #path('advanced/', FSSDrugSearchAPIView.as_view({"post":"post"}), name='drug_search'),
    
    # combine/advanced/
    path('advanced/', ConsolidatedDrugSearchAPIView.as_view({"post":"post"}), name='drug_search'),
    path('advanced/export/', ConsolidatedDrugSearchAPIView.as_view({"post":"export_to_excel"}), name='drug_search_export'),
    #path('combine/advanced/', ConsolidatedDrugSearchAPIView.as_view({"post":"post"}), name='drug_search'),
    path('populate-consolidated/', PopulateConsolidatedTableView.as_view(), name='populate-consolidated'),
]


