# business/views_admin.py
import json
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import connection
from .models import TrainRecord
from .utils import ok, forbidden, unauthorized, parse_date, get_login_ctx

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
