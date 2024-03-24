import random
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from django.shortcuts import redirect, render
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from drf_spectacular.utils import extend_schema
from django.http import JsonResponse
import json
import os
from django.core.files.storage import default_storage

from player.models import Player
from ..serializers import (
    OAuthCodeSerializer,
    OAuthLoginURLSerializer,
    OAuthCallbackSerailizer
)

class OAuthLoginURLView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    @extend_schema(
        responses=OAuthLoginURLSerializer
    )
    def get(self, request, *args, **kwargs):
        client_id = settings.T42_OAUTH2_CLIENT_ID
        client_redirect_uri = settings.T42_OAUTH2_REDIRECT_URI

        t42_oauth2_url = f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}&redirect_uri={client_redirect_uri}&response_type=code"

        return Response({"oauth_login_url":t42_oauth2_url}, status=status.HTTP_200_OK)

class OAuthCallbackView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    @extend_schema(
        request=OAuthCodeSerializer,
        responses=OAuthCallbackSerailizer
    )
    def post(self, request, *args, **kwargs):
        def create_unique_nickname(nickname):
            counter = 1
            while Player.objects.filter(nickname=nickname).exists():
                nickname = nickname + str(counter)
                counter += 1
            return nickname

        authorization_code = request.data.get("code")
        if not authorization_code:
            return Response({"error":"Authorization Code is required"}, status=status.HTTP_400_BAD_REQUEST)

        token_request_data = {
            'code': authorization_code,
            'client_id': settings.T42_OAUTH2_CLIENT_ID,
            'client_secret': settings.T42_OAUTH2_CLIENT_SECRET,
            'redirect_uri': settings.T42_OAUTH2_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        token_response = requests.post('https://api.intra.42.fr/oauth/token', data=token_request_data)

        if token_response.status_code != 200:
            return Response({"error": "Failed to obtain access token"}, status=status.HTTP_400_BAD_REQUEST)

        oauth_access_token = token_response.json().get('access_token')

        user_info_response = requests.get('https://api.intra.42.fr/v2/me',
                                          headers={'Authorization': f'Bearer {oauth_access_token}'})
        if user_info_response.status_code != 200:
            return Response({"error": "Failed to obtain user info"}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        login = user_info.get('login')

        user, created = Player.objects.get_or_create(
            email = user_info.get('email'),
            defaults={
                'nickname': create_unique_nickname(login),
                'last_login_time': timezone.now()
            }
        )
        if created:
            profile_img_url = user_info.get('image', {}).get('link')
            response = requests.get(profile_img_url)
            if response.status_code == 200:
                user.profile_img.save(f'{login}.jpg', ContentFile(response.content), save=True)

        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        if user.profile_img:
            absolute_url = request.build_absolute_uri(user.profile_img.url)
        else:
            absolute_url = None

        response_data = {
            'refresh_token': refresh_token,
            'access_token': access_token,
            'is_new_user': created,
            'user': {
                'id': user.id,
                'nickname': user.nickname,
                'profile_img': absolute_url,
                'intro': user.intro
            }
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        # response.set_cookie(
        #     'refresh_token',  # 쿠키 이름
        #     refresh_token,  # 쿠키 값
        #     httponly=True,  # JavaScript를 통해 쿠키에 접근하는 것을 방지
        #     secure=False,  # HTTPS를 통해서만 쿠키를 전송 - 나중에 HTTPS 설정시 True로 변경
        #     samesite='Lax',  # 쿠키의 SameSite 속성 설정
        #     # max_age, expires 등 추가 설정 가능
        # )

        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token', None)

        if refresh_token is None:
            return Response({"error": "Refresh token is not provided"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

# def home(request):
#     # 홈페이지에 표시할 간단한 메시지
#     return HttpResponse("<h1>Welcome to the homepage!</h1>")

# def t42_login(request):
#     client_id = settings.T42_OAUTH2_CLIENT_ID
#     client_redirect_uri = settings.T42_OAUTH2_REDIRECT_URI
#
#     t42_oauth2_url = f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}&redirect_uri={client_redirect_uri}&response_type=code"
#
#     # 사용자를 인증 URL로 리다이렉션
#     return redirect(t42_oauth2_url)



'''def send_email_with_access_token(access_token):
    # 메일 내용 구성
    email_data = {
        "mailing": {
            "content": "Hi kkk,\nYou just *won* the mego jackpot !\nCheck [this link](http://spam.prizepool-game-lottery.xxx/winner.php)",
            "from": "superwin-ultimate-@prizepool-game-lottery.sexy",
            "identifier": "an_unique_identifier",
            "subject": "You are the super online contest winner !!!",
            "subtitle": "And it's kinda awesome",
            "title": "You won the big jackpot",
            "to": ["andre@42.fr"]
        }
    }

    # 메일 보내기 요청
    response = requests.post(
        'https://api.intra.42.fr/v2/mailings',
        json=email_data,
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # 응답 데이터 반환
    return response.json()'''

def send_email(email_address, subject, message):
    # 이메일 서버 설정
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "wldhel84222@gmail.com"
    smtp_password = "qweo mpyd yvyo pwde"
    
    # MIME 메시지 생성
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_address
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    
    # SMTP 서버를 통해 이메일 전송
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # TLS 보안 시작
    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()


def generate_auth_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))



#@method_decorator(csrf_exempt, name='dispatch')
class VerifyCodePage(generics.GenericAPIView):
    @extend_schema(
        methods=['GET', 'POST'],  # 이 뷰에서 지원하는 메소드
        description='인증 코드를 검증합니다.',
        responses={200: None}  # 응답 스키마 예시
    )
    def get(self, request, *args, **kwargs):
        # 사용자 인증 확인
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)


        user = request.user
        user_email = user.email
        auth_code = generate_auth_code()
        
        user.auth_code = auth_code
        user.save()
    
        send_email(user_email, "Your authentication code", f"Your authentication code is: {auth_code}")
        return JsonResponse({'message': 'Authentication code sent'})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
         # 현재 인증된 사용자를 user 변수에 할당
        user = request.user

        # JSON 데이터 파싱
        data = json.loads(request.body)
        user_input_code = data.get('code')
        expected_code = user.auth_code
       

        if user_input_code == expected_code:
            user.two_factor_auth_enabled = True
            user.auth_code = None  # 인증 코드 사용 후 초기화
            user.save()
            return JsonResponse({'message': 'Authentication successful'})
        else:
            return JsonResponse({'error': 'Invalid authentication code'}, status=400)
        
#@method_decorator(csrf_exempt, name='dispatch')
class DeleteAccount(generics.GenericAPIView):
    @extend_schema(
        methods=['DELETE'],  # 이 뷰에서 지원하는 메소드
        description='계정을 삭제합니다. 이중 인증이 활성화된 계정만 삭제가능',
        responses={200: 'Account successfully deleted'}
    )
    def delete(self, request, *args, **kwargs):
        user = request.user

        if user.two_factor_auth_enabled:
            # delete user profile image from media
            profile_img_path = str(user.profile_img)
            full_profile_img_path = os.path.join(settings.MEDIA_ROOT, profile_img_path)
            if full_profile_img_path and default_storage.exists(full_profile_img_path):
                default_storage.delete(full_profile_img_path)

            user.delete()
            return Response({'message': 'Account successfully deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Two-factor authentication is not enabled. Account deletion is not allowed.'}, status=status.HTTP_403_FORBIDDEN)


# def oauth2callback(request):# 파라미터는 HttpRequest 객체 Django가 자동으로 뷰 함수에 전달됨
#     # 인증 코드 받기
#     code = request.GET.get('code')
#     # 액세스 토큰 요청
#     token_request_data = {
#         'code': code,
#         'client_id': settings.T42_OAUTH2_CLIENT_ID,
#         'client_secret': settings.T42_OAUTH2_CLIENT_SECRET,
#         'redirect_uri': settings.T42_OAUTH2_REDIRECT_URI,
#         'grant_type': 'authorization_code',
#     }
#     token_response = requests.post('https://api.intra.42.fr/oauth/token', data=token_request_data)
#     token_response_data = token_response.json()
#
#     # 액세스 토큰 사용하여 사용자 정보 요청
#     access_token = token_response_data.get('access_token')
#     print(access_token)
#     user_info_response = requests.get('https://api.intra.42.fr/v2/me', headers={'Authorization': f'Bearer {access_token}'})
#     user_info = user_info_response.json()
#     print(user_info)
#     email_address = user_info.get('email')
#     print(email_address)
#
#      # 인증 코드 생성
#     auth_code = generate_auth_code()
#
#     # 인증 코드를 세션에 저장
#     request.session['auth_code'] = auth_code
#
#     subject = "Your authentication code"
#     message = f"Your authentication code is: {auth_code}"
#     send_email(email_address, subject, message)
#     #email_response = send_email_with_access_token(access_token)
#     #print(email_response)
#
#     return redirect('verify_code_page') # get 요청
