from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError
from rest_framework_jwt.settings import api_settings
# class JwtAuthenticationMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         white_list = ["/user/login"]  # 请求白名单
#         path = request.path
#         if path not in white_list and not path.startswith("/media"):
#             print("要进行token验证")
#             # token = request.META.get('HTTP_AUTHORIZATION')
#             token = (
#                     request.META.get('HTTP_AUTHORIZATION')
#                     or request.headers.get('Authorization')
#                     or request.headers.get('authorization')
#             )
#             if token and token.lower().startswith('bearer '):
#                 token = token[7:]
#             print("token:", token)
#             try:
#                 jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
#                 jwt_decode_handler(token)
#             except ExpiredSignatureError:
#                 return HttpResponse('Token过期，请重新登录！')
#             except InvalidTokenError:
#                 return HttpResponse('Token验证失败！')
#             except PyJWTError:
#                 return HttpResponse('Token验证异常！')
#         else:
#             print("不验证验证")
#             return None
# user/middleware.py
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

# djangorestframework-jwt 的设置
from rest_framework_jwt.settings import api_settings

# PyJWT 异常
from jwt import PyJWTError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


class JwtAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        white_list = [
            '/user/login',
            '/user/register',
            '/media/userAvatar',
        ]

        path = request.path
        print("请求路径:", path)

        for white in white_list:
            if path.rstrip('/').startswith(white.rstrip('/')):
                print("白名单放行:", path)
                return None  # 放行

        # 放行预检请求（跨域 OPTIONS）
        if request.method == 'OPTIONS':
            return None

        print("要进行token验证")

        token = (
            request.META.get('HTTP_AUTHORIZATION')
            or request.headers.get('Authorization')
            or request.headers.get('authorization')
        )
        print("token:", token)

        if not token:
            return HttpResponse('未携带Token，请重新登录！', status=401)

        from rest_framework_jwt.settings import api_settings
        from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

        try:
            jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
            payload = jwt_decode_handler(token)
            uid = payload.get('user_id') or payload.get('id') or payload.get('userId')
            request.jwt_user_id = uid
        except ExpiredSignatureError:
            return HttpResponse('Token过期，请重新登录！', status=401)
        except InvalidTokenError:
            return HttpResponse('Token验证失败！', status=401)
        except PyJWTError:
            return HttpResponse('Token验证异常！', status=401)

        return None
