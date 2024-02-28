from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import redirect, render
from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import random
import string

class OAuthLoginURLView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        client_id = settings.T42_OAUTH2_CLIENT_ID
        client_redirect_uri = settings.T42_OAUTH2_REDIRECT_URI

        t42_oauth2_url = f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}&redirect_uri={client_redirect_uri}&response_type=code"

        return Response({"oauth_login_url":t42_oauth2_url}, status=status.HTTP_200_OK)

# class OAuthCallbackView(generics.GenericAPIView):
#     def post(self, request, *args, **kwargs):
#         authorization_code = request.data["code"]
#         if not authorization_code:
#             return Response({"error":"Authorization Code is required"}, status=status.HTTP_400_BAD_REQUEST)
#
#         token_request_data = {
#             'code': authorization_code,
#             'client_id': settings.T42_OAUTH2_CLIENT_ID,
#             'client_secret': settings.T42_OAUTH2_CLIENT_SECRET,
#             'redirect_uri': settings.T42_OAUTH2_REDIRECT_URI,
#             'grant_type': 'authorization_code',
#         }
#         token_response = requests.post('https://api.intra.42.fr/oauth/token', data=token_request_data)
#
#         if token_response.status_code != 200:
#             return Response({"error": "Failed to obtain access token"}, status=status.HTTP_400_BAD_REQUEST)
#
#         oauth_access_token = token_response.json().get('access_token')
#
#         user_info_response = requests.get('https://api.intra.42.fr/v2/me',
#                                           headers={'Authorization': f'Bearer {oauth_access_token}'})
#         if user_info_response.status_code != 200:
#             return Response({"error": "Failed to obtain user info"}, status=status.HTTP_400_BAD_REQUEST)
#
#         user_info = user_info_response.json()
#         login = user_info.get('login')
#         email = user_info.get('email')
#         profile_img = user_info.get('image', {}).get('link')
#
#         # 이메일을 통해 해당 유저가 이미 가입되어있는지 확인
#
#         access_token = generate_auth_code()
#
#         return Response({"access_token": access_token}, status=status.HTTP_200_OK)



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


def verify_code_page(request):
    if request.method == 'POST':
        # 사용자 입력 인증 코드
        user_input_code = request.POST.get('code')
        # 세션에 저장된 인증 코드
        expected_code = request.session.get('auth_code')

        if user_input_code == expected_code:
            # 인증 코드가 일치하는 경우
            del request.session['auth_code']  # 세션에서 인증 코드 삭제
            # 인증 성공 처리, 예를 들어 사용자를 홈페이지로 리다이렉션
            return redirect('home')
        else:
            # 인증 코드가 일치하지 않는 경우
            # 에러 메시지와 함께 다시 인증 코드 입력 페이지를 렌더링
            return render(request, 'tcen_auth/verify_code.html', {'error': 'Invalid authentication code. Please try again.'})
    else:
        # GET 요청인 경우, 인증 코드 입력 폼을 렌더링
        return render(request, 'tcen_auth/verify_code.html')





def oauth2callback(request):# 파라미터는 HttpRequest 객체 Django가 자동으로 뷰 함수에 전달됨
    # 인증 코드 받기
    code = request.GET.get('code')
    # 액세스 토큰 요청
    token_request_data = {
        'code': code,
        'client_id': settings.T42_OAUTH2_CLIENT_ID,
        'client_secret': settings.T42_OAUTH2_CLIENT_SECRET,
        'redirect_uri': settings.T42_OAUTH2_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    token_response = requests.post('https://api.intra.42.fr/oauth/token', data=token_request_data)
    token_response_data = token_response.json()
    
    # 액세스 토큰 사용하여 사용자 정보 요청
    access_token = token_response_data.get('access_token')
    print(access_token)
    user_info_response = requests.get('https://api.intra.42.fr/v2/me', headers={'Authorization': f'Bearer {access_token}'})
    user_info = user_info_response.json()
    print(user_info)
    email_address = user_info.get('email')
    print(email_address)
    
     # 인증 코드 생성
    auth_code = generate_auth_code()
    
    # 인증 코드를 세션에 저장
    request.session['auth_code'] = auth_code
    
    subject = "Your authentication code"
    message = f"Your authentication code is: {auth_code}"
    send_email(email_address, subject, message)
    #email_response = send_email_with_access_token(access_token)
    #print(email_response)

    return redirect('verify_code_page') # get 요청
