from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from config import settings


admin.site.site_header = "Administration Ahsxpress"
admin.site.site_title = "Ashxpress"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('store.urls')),
    #path("ckeditor5/", include('django_ckeditor_5.urls')),

]