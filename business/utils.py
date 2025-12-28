import datetime
from django.http import JsonResponse
from rest_framework.settings import api_settings

from role.models import SysRole


#通用工具，统一返回，取用户，解析日期
def ok(data): return JsonResponse({"code":200, "msg":"ok", "data":data}, json_dumps_params={"ensure_ascii":False})
def bad(msg): return JsonResponse({"code":400, "msg":str(msg)}, json_dumps_params={"ensure_ascii":False})
def unauthorized(): return JsonResponse({"code":401, "msg":"unauthorized"})
def forbidden(): return JsonResponse({"code":403, "msg":"forbidden"})

def parse_date(s: str|None) -> datetime.date|None:
    if not s: return None
    return datetime.date.fromisoformat(s)

def get_login_ctx(request): #这里采取的方法是访问登录账号的user_id 然后登录账号的role是不是管理员，是的话就
    """
    返回 (uid, role_code)
    - 先尝试从 request 上取（若将来中间件写入了）
    - 取不到则自己从 Authorization 里解 JWT
    - 角色优先从数据库 (SysUserRole -> SysRole.code) 反查；查不到再从 payload 兜底
    """
    #傻逼,request又没有role
    # 1) 若中间件以后写入了，优先用
    uid = getattr(request, "jwt_user_id", None)
    if uid:
        role_codes = list(
            SysRole.objects.filter(sysuserrole__user_id=uid)
            .values_list("code", flat=True)
        )
        role = role_codes[0].lower() if role_codes else None
        return uid, role

    # 2) 自己解 JWT
    token = (request.META.get("HTTP_AUTHORIZATION") or "").strip()
    if not token:
        return None, None

    # 兼容前端如果误传了 "Bearer xxx"
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    try:
        payload = api_settings.JWT_DECODE_HANDLER(token)
    except Exception:
        return None, None

    # 兼容不同字段名
    uid = (
        payload.get("user_id")
        or payload.get("id")
        or payload.get("uid")
        or payload.get("userId")
    )
    if not uid:
        return None, None

    # 3) 用 uid 反查角色 code
    role_codes = list(
        SysRole.objects.filter(sysuserrole__user_id=uid)
        .values_list("code", flat=True)
    )

    # 4) 查不到再从 payload 兜底（兼容老 token）
    if not role_codes:
        pr = payload.get("role") or payload.get("role_code")
        if pr:
            role_codes = [pr]

    role = role_codes[0].lower() if role_codes else None
    return uid, role
