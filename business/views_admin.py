# business/views_admin.py
import json
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import connection
from django.utils import timezone  # // <--- 新增代码
from .models import TrainRecord, LeaveRequest  # // <--- 新增代码
from .utils import ok, bad, forbidden, unauthorized, parse_date, get_login_ctx  # // <--- 新增代码
from user.models import SysUser  # // <--- 新增代码


class AdminSearchView(View):
    """
    POST /bsns/training/admin/search
    body:
    {
      "pageNum":1,"pageSize":10,
      "userId":null, "username":"", "studentNo":"",
      "from":"YYYY-MM-DD","to":"YYYY-MM-DD",
      "minMinutes":null,"maxMinutes":null,
      "order":"date_desc"
    }
    返回：{ total, rows:[{id,user_id,username,student_no,date,minutes,source}] }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()
        if role not in ("admin","administrator","superadmin"):
            print("role: "+str(role))
            return forbidden()

        data = json.loads(request.body.decode("utf-8") or "{}")
        pageNum  = int(data.get("pageNum", 1))
        pageSize = int(data.get("pageSize", 10))
        userId     = data.get("userId")
        username   = (data.get("username") or "").strip()
        student_no = (data.get("studentNo") or "").strip()
        qf = parse_date(data.get("from"))
        qt = parse_date(data.get("to"))
        minM = data.get("minMinutes")
        maxM = data.get("maxMinutes")
        order = "-date" if data.get("order","date_desc")=="date_desc" else "date"


        from user.models import SysUser  # 你的用户模型路径按实际调整
        qs = (TrainRecord.objects
              .all()
              .select_related(None))  # 保持轻量

        if userId:     qs = qs.filter(user_id=userId)
        if qf and qt:  qs = qs.filter(date__range=[qf, qt])
        if minM is not None: qs = qs.filter(minutes__gte=minM)
        if maxM is not None: qs = qs.filter(minutes__lte=maxM)

        # username/student_no 需要对照 sys_user；先把符合条件的 user_id 算出来
        user_ids = None
        if username or student_no:
            uqs = SysUser.objects.all()
            if username:
                uqs = uqs.filter(username__icontains=username)
            if student_no:
                uqs = uqs.filter(student_no=student_no)
            user_ids = list(uqs.values_list("id", flat=True))
            if not user_ids:  # 没有匹配用户，直接返回空
                return ok({"total":0,"pageNum":pageNum,"pageSize":pageSize,"rows":[]})
            qs = qs.filter(user_id__in=user_ids)

        qs = qs.order_by(order, "-id")
        total = qs.count()
        pg = Paginator(qs, pageSize).page(pageNum)

        # 为了带回 username/student_no，这里做一次 user_id→信息 的映射
        user_info_map = {}
        if user_ids is None:
            # 这一页涉及到的用户
            user_ids = list(set([r.user_id for r in pg.object_list]))
        if user_ids:
            urows = SysUser.objects.filter(id__in=user_ids).values("id","username","student_no")
            user_info_map = {u["id"]: (u["username"], u.get("student_no")) for u in urows}

        rows = []
        for r in pg.object_list:
            username, sno = user_info_map.get(r.user_id, (None, None))
            rows.append({
                "id": r.id, "user_id": r.user_id,
                "username": username, "student_no": sno,
                "date": r.date, "minutes": r.minutes, "source": r.source
            })

        return ok({"total": total, "pageNum": pageNum, "pageSize": pageSize, "rows": rows})


class LeaveAdminListView(View):
    """
    POST /bsns/leave/admin/list
    body:
    {
      "pageNum":1,
      "pageSize":10,
      "userId": null,        # 可选：按用户 ID 精确过滤
      "username": "",        # 可选：按用户名模糊查询
      "studentNo": "",       # 可选：按学号精确查询
      "status": "pending",   # 可选：pending/approved/rejected/cancelled
      "from": "YYYY-MM-DD",  # 可选：按 start_date 起始过滤
      "to": "YYYY-MM-DD"     # 可选：按 start_date 结束过滤
    }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()
        if role not in ("admin", "administrator", "superadmin"):
            return forbidden()

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return bad("请求体必须是 JSON")

        pageNum = int(data.get("pageNum") or 1)
        pageSize = int(data.get("pageSize") or 10)
        if pageNum <= 0:
            pageNum = 1
        if pageSize <= 0 or pageSize > 200:
            pageSize = 10

        user_id = data.get("userId")
        username = (data.get("username") or "").strip()
        student_no = (data.get("studentNo") or "").strip()
        status = (data.get("status") or "").strip().lower()

        if status and status not in ("pending", "approved", "rejected", "cancelled"):
            return bad("status 不合法")

        qf = parse_date(data.get("from"))
        qt = parse_date(data.get("to"))

        qs = LeaveRequest.objects.all()

        # 按用户 ID 过滤
        if user_id:
            qs = qs.filter(user_id=user_id)

        # 按用户名/学号过滤 -> 先查出对应的 user_id 列表
        if username or student_no:
            uqs = SysUser.objects.all()
            if username:
                uqs = uqs.filter(username__icontains=username)
            if student_no:
                uqs = uqs.filter(student_no=student_no)
            user_ids = list(uqs.values_list("id", flat=True))
            if not user_ids:
                return ok({
                    "total": 0,
                    "pageNum": pageNum,
                    "pageSize": pageSize,
                    "rows": [],
                })
            qs = qs.filter(user_id__in=user_ids)

        # 按状态过滤
        if status:
            qs = qs.filter(status=status)

        # 按请假开始日期区间过滤
        if qf and qt:
            qs = qs.filter(start_date__range=[qf, qt])

        qs = qs.order_by("-create_time", "-id")
        total = qs.count()

        pg = Paginator(qs, pageSize).page(pageNum)

        # 拼接用户信息（用户名 & 学号）
        user_ids = [r.user_id for r in pg.object_list]
        user_info_map = {}
        if user_ids:
            urows = SysUser.objects.filter(id__in=user_ids).values("id", "username", "student_no")
            user_info_map = {u["id"]: (u["username"], u.get("student_no")) for u in urows}

        rows = []
        for r in pg.object_list:
            username, sno = user_info_map.get(r.user_id, (None, None))
            rows.append({
                "id": r.id,
                "user_id": r.user_id,
                "username": username,
                "student_no": sno,
                "startDate": r.start_date,
                "endDate": r.end_date,
                "status": r.status,
                "reason": r.reason,
                "adminComment": r.admin_comment,
                "requestTime": r.create_time,
                "decisionTime": r.decision_time,
                "cancelTime": r.cancel_time,
            })

        return ok({
            "total": total,
            "pageNum": pageNum,
            "pageSize": pageSize,
            "rows": rows,
        })


# // <--- 新增代码
class LeaveAdminApproveView(View):
    """
    POST /bsns/leave/admin/approve
    body:
    {
      "id": 123,
      "action": "approve",     # "approve" 或 "reject"
      "comment": "可选，审批意见"
    }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()
        if role not in ("admin", "administrator", "superadmin"):
            return forbidden()

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return bad("请求体必须是 JSON")

        rid = data.get("id")
        action = (data.get("action") or "").strip().lower()
        comment = (data.get("comment") or "").strip()

        if not rid:
            return bad("缺少 id")
        if action not in ("approve", "reject"):
            return bad("action 必须为 approve 或 reject")

        try:
            obj = LeaveRequest.objects.get(id=rid)
        except LeaveRequest.DoesNotExist:
            return bad("记录不存在")

        if obj.status != "pending":
            return bad("当前状态不允许审批")

        if action == "approve":
            obj.status = "approved"
        else:
            obj.status = "rejected"

        obj.admin_comment = comment or None
        obj.decision_time = timezone.now()
        obj.save(update_fields=["status", "admin_comment", "decision_time", "update_time"])

        return ok({
            "id": obj.id,
            "status": obj.status,
            "adminComment": obj.admin_comment,
            "decisionTime": obj.decision_time,
        })
