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
        white_list = ["/user/login"]  # 请求白名单
        path = request.path

        # ① 放行 CORS 预检（浏览器带 Authorization 会先发 OPTIONS）
        if request.method == 'OPTIONS':
            return None

        if path not in white_list and not path.startswith("/media"):
            # ② 更稳妥读取 Authorization
            token = (
                request.META.get('HTTP_AUTHORIZATION')
                or request.headers.get('Authorization')
                or request.headers.get('authorization')
            )
            # print("token:", token)

            if not token:
                return HttpResponse('未携带Token，请重新登录！', status=401)

            # 兼容 Bearer/Token 前缀（前端随便传）
            low = token.lower()
            if low.startswith('bearer '):
                token = token[7:]
            elif low.startswith('token '):
                token = token[6:]

            try:
                # ③ 解码 token
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                payload = jwt_decode_handler(token)

                # ④ **把 user_id 挂到 request 上**（视图里的 get_login_ctx 就能取到了）
                # djangorestframework-jwt 的默认载荷里是 'user_id'
                uid = payload.get('user_id') or payload.get('id') or payload.get('userId')
                if not uid:
                    return HttpResponse('Token缺少user_id！', status=401)

                # 供 business/utils.get_login_ctx 使用
                request.jwt_user_id = uid
                request.jwt_role_code = payload.get('role') or ''

            except ExpiredSignatureError:
                return HttpResponse('Token过期，请重新登录！', status=401)
            except InvalidTokenError:
                return HttpResponse('Token验证失败！', status=401)
            except PyJWTError:
                return HttpResponse('Token验证异常！', status=401)

        return None
