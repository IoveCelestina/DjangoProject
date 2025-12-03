import datetime
from django.views import View
from django.db.models import Sum
from django.utils import timezone
from .models import TrainRecord,LeaveRequest
from .utils import ok, bad, unauthorized, parse_date, get_login_ctx
import json
from django.core.paginator import Paginator
from user.models import SysUser
class MyOverviewView(View):
    """
    GET /bsns/training/my/overview?from=YYYY-MM-DD&to=YYYY-MM-DD
    返回：
    {
      total_minutes, total_days, avg_minutes_per_day,
      by_date: [{date, minutes}]
    }
    """
    def get(self, request):
        uid, _ = get_login_ctx(request)
        if not uid:
            return unauthorized()

        qf = parse_date(request.GET.get("from"))
        qt = parse_date(request.GET.get("to"))
        if not qf or not qt:
            qt = datetime.date.today()
            qf = qt - datetime.timedelta(days=30)

        qs = TrainRecord.objects.filter(user_id=uid, date__range=[qf, qt])
        total = qs.aggregate(s=Sum("minutes"))["s"] or 0
        days  = qs.values("date").distinct().count()
        daily = list(qs.values("date").annotate(minutes=Sum("minutes")).order_by("date"))
        user = SysUser.objects.filter(id=uid).only("violation_count").first()   #获取当前用户的违规次数
        violation_count = user.violation_count if user else 0
        return ok({
            "total_minutes": total,
            "total_days": days,
            "avg_minutes_per_day": round(total/max(days,1), 1),
            "by_date": [{"date": str(d["date"]), "minutes": d["minutes"]} for d in daily],
            "violation_count": violation_count
        })




class MyListView(View):
    """
    POST /bsns/training/my/list
    body:
    {
      "pageNum":1,"pageSize":10,
      "from":"YYYY-MM-DD","to":"YYYY-MM-DD",
      "source":"", "order":"date_desc"
    }
    返回：{ total, pageNum, pageSize, rows:[{id,date,minutes,source}] }
    """
    def post(self, request):
        uid, _ = get_login_ctx(request)
        if not uid:
            return unauthorized()

        data = json.loads(request.body.decode("utf-8") or "{}")
        pageNum  = int(data.get("pageNum", 1))
        pageSize = int(data.get("pageSize", 10))
        qf = parse_date(data.get("from"))
        qt = parse_date(data.get("to"))
        source = data.get("source")
        order = "-date" if data.get("order","date_desc")=="date_desc" else "date"

        qs = TrainRecord.objects.filter(user_id=uid)
        if qf and qt: qs = qs.filter(date__range=[qf, qt])
        if source:   qs = qs.filter(source=source)
        qs = qs.order_by(order, "-id")

        pg = Paginator(qs, pageSize).page(pageNum)
        rows = list(pg.object_list.values("id","date","minutes","source"))

        return ok({"total": qs.count(), "pageNum": pageNum, "pageSize": pageSize, "rows": rows})

class MyLeaveAddView(View):
    """
    POST /bsns/leave/my/add
    body:
    {
      "startDate": "YYYY-MM-DD",
      "endDate": "YYYY-MM-DD",
      "reason": "可选，请假理由"
    }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return bad("请求体必须是 JSON")

        start_date_str = data.get("from") or data.get("startDate")
        end_date_str = data.get("to") or data.get("endDate")
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        reason = (data.get("reason") or "").strip()

        if not start_date or not end_date:
            return bad("startDate 和 endDate 必填")
        if end_date < start_date:
            return bad("endDate 不能早于 startDate")
        if len(reason) > 500:
            return bad("reason 过长")

        obj = LeaveRequest.objects.create(
            user_id=uid,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            reason=reason or None,
        )

        return ok({
            "id": obj.id,
            "startDate": obj.start_date,
            "endDate": obj.end_date,
            "status": obj.status,
            "reason": obj.reason,
            "adminComment": obj.admin_comment,
            "requestTime": obj.create_time,
            "decisionTime": obj.decision_time,
            "cancelTime": obj.cancel_time,
        })


class MyLeaveCancelView(View):
    """
    POST /bsns/leave/my/cancel
    body:
    {
      "id": 123
    }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return bad("请求体必须是 JSON")

        rid = data.get("id")
        if not rid:
            return bad("缺少 id")

        try:
            obj = LeaveRequest.objects.get(id=rid, user_id=uid)
        except LeaveRequest.DoesNotExist:
            return bad("记录不存在")

        if obj.status != "pending":
            return bad("当前状态不允许取消")

        obj.status = "cancelled"
        obj.cancel_time = timezone.now()
        obj.save(update_fields=["status", "cancel_time", "update_time"])

        return ok({
            "id": obj.id,
            "status": obj.status,
            "cancelTime": obj.cancel_time,
        })


# // <--- 新增代码
class MyLeaveListView(View):
    """
    POST /bsns/leave/my/list
    body:
    {
      "pageNum": 1,
      "pageSize": 10,
      "status": "pending",      # 可选：pending/approved/rejected/cancelled
      "from": "YYYY-MM-DD",     # 可选：按 start_date 起始过滤
      "to": "YYYY-MM-DD"        # 可选：按 start_date 结束过滤
    }
    """
    def post(self, request):
        uid, role = get_login_ctx(request)
        if not uid:
            return unauthorized()

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return bad("请求体必须是 JSON")

        pageNum = int(data.get("pageNum") or 1)
        pageSize = int(data.get("pageSize") or 10)
        if pageNum <= 0:
            pageNum = 1
        if pageSize <= 0 or pageSize > 100:
            pageSize = 10

        status = (data.get("status") or "").strip().lower()
        if status and status not in ("pending", "approved", "rejected", "cancelled"):
            return bad("status 不合法")

        qf = parse_date(data.get("from"))
        qt = parse_date(data.get("to"))

        qs = LeaveRequest.objects.filter(user_id=uid)
        if status:
            qs = qs.filter(status=status)
        if qf and qt:
            qs = qs.filter(start_date__range=[qf, qt])

        qs = qs.order_by("-create_time", "-id")

        pg = Paginator(qs, pageSize).page(pageNum)
        rows = []
        for r in pg.object_list:
            rows.append({
                "id": r.id,
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
            "total": qs.count(),
            "pageNum": pageNum,
            "pageSize": pageSize,
            "rows": rows,
        })
