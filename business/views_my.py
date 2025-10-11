import datetime
from django.views import View
from django.db.models import Sum
from .models import TrainRecord
from .utils import ok, bad, unauthorized, parse_date, get_login_ctx
import json
from django.core.paginator import Paginator
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

        return ok({
            "total_minutes": total,
            "total_days": days,
            "avg_minutes_per_day": round(total/max(days,1), 1),
            "by_date": [{"date": str(d["date"]), "minutes": d["minutes"]} for d in daily]
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
