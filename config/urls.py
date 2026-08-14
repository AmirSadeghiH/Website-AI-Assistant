from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from chat.admin import admin_site


urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/', include("chat.urls")),
    path('demo/', RedirectView.as_view(url='/static/demo.html', permanent=False)),
    path('', RedirectView.as_view(url='/static/demo.html', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
