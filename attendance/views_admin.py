# attendance/views_admin.py
from __future__ import annotations

from typing import Any, Dict, Optional

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from attendance.crypto_utils import encrypt_trust_code
from attendance.models import AttendanceAuthConfig, AttendanceSyncJob, AttendanceSyncState
from attendance.pipeline_service import run_attendance_pipeline
from attendance.attendance_client import AttendanceClientError


def _ok(data: Any = None, msg: str = "") -> JsonResponse:
    return JsonResponse({"code": 0, "msg": msg, "data": data})


def _err(msg: str, code: int = 1, data: Any = None) -> JsonResponse:
    return JsonResponse({"code": code, "msg": msg, "data": data})


def _get_user_id_from_request(request) -> Optional[int]:
    """
    兼容你现有 JWT 中间件：尽量从 request.user 或 request.user_id 取
    如果你项目里是 request.user.id，则直接可用。
    """
    u = getattr(request, "user", None)
    if u is not None:
        uid = getattr(u, "id", None)
        if uid is not None:
            return int(uid)
    uid = getattr(request, "user_id", None)
    if uid is not None:
        return int(uid)
    return None


@csrf_exempt
@require_POST
def save_trust_code(request):
    """
    POST /bsns/attendance/admin/trust_code
    body:
      - trust_code: string
      - run_pipeline: bool (default true)
    """
    try:
        import json

        body = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        body = {}

    trust_code = (body.get("trust_code") or "").strip()
    run_pipeline_flag = body.get("run_pipeline", True)

    if not trust_code:
        return _err("trust_code 不能为空")

    # 保存配置（密文）
    cfg = AttendanceAuthConfig.objects.first() or AttendanceAuthConfig.objects.create()
    cfg.trust_code_cipher = encrypt_trust_code(trust_code)
    cfg.updated_by = _get_user_id_from_request(request)
    cfg.last_error = None
    cfg.updated_at = timezone.now()
    cfg.save()

    # 可选：立即跑流水线（采集+计算+回写）
    if not run_pipeline_flag:
        return _ok({"saved": True}, "已保存 trust_code")

    try:
        result = run_attendance_pipeline(created_by=cfg.updated_by)
        return _ok(
            {
                "job_id": result.job_id,
                "inserted_count": result.inserted_count,
                "updated_count": result.updated_count,
                "computed_days": result.computed_days,
                "written_records": result.written_records,
            },
            "流水线执行成功",
        )
    except AttendanceClientError as e:
        return _err(f"流水线执行失败：{str(e)}")
    except Exception as e:
        return _err(f"内部错误：{str(e)}")


@csrf_exempt
@require_POST
def run_pipeline(request):
    """
    POST /bsns/attendance/admin/pipeline/run
    自动回补缺口（上次成功到现在；无上次则 30 天）
    """
    uid = _get_user_id_from_request(request)
    try:
        result = run_attendance_pipeline(created_by=uid)
        return _ok(
            {
                "job_id": result.job_id,
                "inserted_count": result.inserted_count,
                "updated_count": result.updated_count,
                "computed_days": result.computed_days,
                "written_records": result.written_records,
            },
            "流水线执行成功",
        )
    except AttendanceClientError as e:
        return _err(f"流水线执行失败：{str(e)}")
    except Exception as e:
        return _err(f"内部错误：{str(e)}")


@require_GET
def pipeline_state(request):
    """
    GET /bsns/attendance/admin/pipeline/state
    返回：
      - last_success_at
      - default_backfill_days
      - safety_buffer_minutes
      - need_trust_code
      - last_job (最近一条任务)
    """
    cfg = AttendanceAuthConfig.objects.first()
    state = AttendanceSyncState.objects.first()

    need_trust_code = not (cfg and cfg.trust_code_cipher)

    last_job = AttendanceSyncJob.objects.order_by("-create_time").first()
    last_job_data: Dict[str, Any] = {}
    if last_job:
        last_job_data = {
            "job_id": last_job.job_id,
            "status": last_job.status,
            "range_start": last_job.range_start.strftime("%Y-%m-%d %H:%M:%S") if last_job.range_start else None,
            "range_end": last_job.range_end.strftime("%Y-%m-%d %H:%M:%S") if last_job.range_end else None,
            "inserted_count": last_job.inserted_count,
            "updated_count": last_job.updated_count,
            "error_code": last_job.error_code,
            "error_message": last_job.error_message,
            "started_at": last_job.started_at.strftime("%Y-%m-%d %H:%M:%S") if last_job.started_at else None,
            "finished_at": last_job.finished_at.strftime("%Y-%m-%d %H:%M:%S") if last_job.finished_at else None,
        }

    data = {
        "need_trust_code": need_trust_code,
        "last_error": cfg.last_error if cfg else None,
        "last_verified_at": cfg.last_verified_at.strftime("%Y-%m-%d %H:%M:%S") if (cfg and cfg.last_verified_at) else None,
        "last_success_at": state.last_success_at.strftime("%Y-%m-%d %H:%M:%S") if (state and state.last_success_at) else None,
        "default_backfill_days": state.default_backfill_days if state else 30,
        "safety_buffer_minutes": state.safety_buffer_minutes if state else 30,
        "last_job": last_job_data,
    }
    return _ok(data)


@require_GET
def jobs(request):
    """
    GET /bsns/attendance/admin/pipeline/jobs?page_num=1&page_size=20
    """
    try:
        page_num = int(request.GET.get("page_num") or 1)
        page_size = int(request.GET.get("page_size") or 20)
    except Exception:
        page_num, page_size = 1, 20

    if page_num < 1:
        page_num = 1
    if page_size < 1 or page_size > 200:
        page_size = 20

    qs = AttendanceSyncJob.objects.order_by("-create_time")
    total = qs.count()
    start = (page_num - 1) * page_size
    items = qs[start : start + page_size]

    rows = []
    for j in items:
        rows.append(
            {
                "job_id": j.job_id,
                "status": j.status,
                "range_start": j.range_start.strftime("%Y-%m-%d %H:%M:%S") if j.range_start else None,
                "range_end": j.range_end.strftime("%Y-%m-%d %H:%M:%S") if j.range_end else None,
                "inserted_count": j.inserted_count,
                "updated_count": j.updated_count,
                "error_code": j.error_code,
                "error_message": j.error_message,
                "create_time": j.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return _ok({"total": total, "rows": rows})


@require_GET
def job_detail(request, job_id: str):
    """
    GET /bsns/attendance/admin/pipeline/jobs/<job_id>
    """
    j = AttendanceSyncJob.objects.filter(job_id=job_id).first()
    if not j:
        return _err("任务不存在")

    data = {
        "job_id": j.job_id,
        "status": j.status,
        "range_start": j.range_start.strftime("%Y-%m-%d %H:%M:%S") if j.range_start else None,
        "range_end": j.range_end.strftime("%Y-%m-%d %H:%M:%S") if j.range_end else None,
        "cursor_day": j.cursor_day.strftime("%Y-%m-%d") if j.cursor_day else None,
        "cursor_page": j.cursor_page,
        "inserted_count": j.inserted_count,
        "updated_count": j.updated_count,
        "error_code": j.error_code,
        "error_message": j.error_message,
        "created_by": j.created_by,
        "started_at": j.started_at.strftime("%Y-%m-%d %H:%M:%S") if j.started_at else None,
        "finished_at": j.finished_at.strftime("%Y-%m-%d %H:%M:%S") if j.finished_at else None,
        "create_time": j.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "update_time": j.update_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return _ok(data)
