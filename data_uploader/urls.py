from django.urls import path
from .views import *

urlpatterns = [
    
    path('upload/dod/file/', UploadDataDODFileView.as_view(), name='upload-dod-data'),
    path('upload/foia/file/', UploadDataDODFileView.as_view(), name='upload-foia-data'),
    path('update/fss/notes/', FSSDrugUpdateNotesView.as_view(), name='update-fss'),
    path('update/foia/notes/', FOIADrugUpdateNotesView.as_view(), name='update-fss'),
    path('update/vendor/notes/', FSSVendorUpdateNotesView.as_view(), name='update-Vendor'),
    path('update/fss/manufacturer/', ManufacturerUpdateView.as_view(), name='update-manufacturer'),
    path('update/fss/<int:pk>/info/', FSSDrugUpdateView.as_view(), name='update-fss'),
    path('upload/foia/monthly-stats/', FOIAMonthlyStatsFileUploadView.as_view(), name='foia-monthly-stats'),

]