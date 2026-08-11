from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("chat.urls")),
    path('demo/', RedirectView.as_view(url='/static/demo.html', permanent=False)),
    path('', RedirectView.as_view(url='/static/demo.html', permanent=False)),
]
