from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from rest_framework_jwt.settings import api_settings

# PyJWT 的异常
from jwt import PyJWTError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


class JwtAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        white_list = ["/user/login"]
        path = request.path

        # 1) 放行 CORS 预检（否则浏览器带 Authorization 会先发 OPTIONS，被拦成 401）
        if request.method == 'OPTIONS':
            return None

        if path not in white_list and not path.startswith("/media"):
            print("要进行token验证")

            # 2) 更稳地读取 Authorization（兼容不同环境）
            token = (
                request.META.get('HTTP_AUTHORIZATION')
                or request.headers.get('Authorization')
                or request.headers.get('authorization')
            )
            print("token:", token)

            if not token:
                return HttpResponse('未携带Token，请重新登录！', status=401)

            # 3) 兼容 Bearer/Token 前缀，前端随便传哪种都能解
            low = token.lower()
            if low.startswith('bearer '):
                token = token[7:]
            elif low.startswith('token '):
                token = token[6:]

            try:
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                jwt_decode_handler(token)
            except ExpiredSignatureError:
                return HttpResponse('Token过期，请重新登录！', status=401)
            except InvalidTokenError:
                return HttpResponse('Token验证失败！', status=401)
            except PyJWTError:
                return HttpResponse('Token验证异常！', status=401)

        return None
