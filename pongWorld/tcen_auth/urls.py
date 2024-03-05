from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    #path('admin/', admin.site.urls),
    #path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')), 이 구문은 리소스 서버의 역할을 할때 사용함 지금은 필요없음
    path('42-login/', views.OAuthLoginURLView.as_view(), name='42_login'),
    path('pong-world-login/', views.OAuthCallbackView.as_view(), name='pong_world_login'),
    path('refresh-token/', views.TokenRefreshView.as_view(), name='token_refresh'),
    # path('verify/', views.tcen_auth.verify_code_page, name='verify_code_page'),
    # path('', views.home, name='home'),
]

