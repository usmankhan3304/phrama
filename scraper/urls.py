from django.urls import path
from .views import *

urlpatterns = [
    path('start/scraping/', PharmaScraperView.as_view(), name='start-scraping'),
    path('stop/scraping/', StopScrapingView.as_view(), name='stop-scraping'),
    path('insert/scraped/data/', InsertScrapedDataView.as_view(), name='insert-scraped-data'),
    path('insert/foia/data/', InsertFOIADataView.as_view(), name='insert-foia-data'),
    path('insert/dod/data/', InsertDODDrugDataView.as_view(), name='insert-dod-data'),
]
