from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from chat.admin import admin_site

urlpatterns = [
    # Only the custom panel is the product face. The Django admin stays
    # reachable at /admin/ for technical maintenance but is not linked
    # anywhere in the panel UI any more.
    path('admin/', admin_site.urls),
    path('panel/', include("chat.panel_urls")),
    path('api/', include("chat.urls")),
    # Themed demo page: serves static/demo.html with the widget bundle
    # matching the panel-selected UI variant.
    path('demo/', RedirectView.as_view(url='/api/demo/', permanent=False)),
    path('', RedirectView.as_view(url='/panel/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
