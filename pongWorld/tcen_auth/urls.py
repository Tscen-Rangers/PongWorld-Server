"""auth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path, include
from . import views

urlpatterns = [
    #path('admin/', admin.site.urls),
    #path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')), 이 구문은 리소스 서버의 역할을 할때 사용함 지금은 필요없음
    path('42-login/', views.OAuthLoginURLView.as_view(), name='42_login'),
    path('callback/', views.oauth2callback, name='callback'), # 첫번째 인자는 사용자 인증으로 넘길때 내가 설정한 url
    path('verify/', views.verify_code_page, name='verify_code_page'),
    # path('', views.home, name='home'),
]


