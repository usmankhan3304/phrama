"""
URL configuration for confg_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from confg_django.settings import BASE_URL
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from drf_yasg import openapi
from .schemaProtocal import BothHttpAndHttpsSchemaGenerator
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    generator_class=BothHttpAndHttpsSchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
    url=BASE_URL,
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include(('auth_manager.urls', 'auth_manager'), namespace='api_auth')),
    path('api/scraper/', include(('scraper.urls', 'scraper'), namespace='scraper')),
    path('api/data-provider/', include(('data_provider.urls', 'data_provider'), namespace='data_provider')),
    path('api/data/', include(('data_uploader.urls', 'data_uploader'), namespace='data_uploader')),
    path('api/search/', include(('smart_search.urls', 'smart_search'), namespace='smart_search')),
    
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
