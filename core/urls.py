from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Default Admin
    path('admin/', admin.site.urls),

    # Hamari App ki APIs aur Custom Dashboard
    path('api/', include('api.urls')),
]

# Images display karne ke liye
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)