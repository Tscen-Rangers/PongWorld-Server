from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = routers.DefaultRouter()
app_name = 'player'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('player/', include(('player.urls', 'api'))),
    path('chat/', include('chat.urls')),
    path('tcen-auth/', include('tcen_auth.urls')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^schema(?P<format>\.json|\.yaml)$', SpectacularAPIView.as_view(), name='schema-json'),
    ]
