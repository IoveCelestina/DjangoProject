# attendance/pipeline_service.py
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.apps import apps
from django.db import connection, transaction
from django.utils import timezone

from attendance.attendance_client import AttendanceClient, AttendanceClientError
from attendance.crypto_utils import decrypt_trust_code
from attendance.models import (
    AttendanceAuthConfig,
    AttendanceCheckin,
    AttendanceSyncJob,
    AttendanceSyncState,
)


@dataclass
class PipelineResult:
    job_id: str
    inserted_count: int
    updated_count: int
    computed_days: int
    written_records: int


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_dedupe_key(
    org_id: str,
    student_no: str,
    check_in_time_ms: int,
    checkin_type: str,
    source: str,
) -> str:
    """
    宽松但不重复的去重指纹：
    - 不依赖 terminal_id/device_name（避免字段不稳定导致重复）
    - 依赖时间戳毫秒 + 类型 + 来源，重复概率极低
    """
    raw = f"{org_id}|{student_no}|{check_in_time_ms}|{checkin_type}|{source}"
    return _sha256_hex(raw)


def _to_dt_from_ms(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.get_current_timezone())


def _day_ranges(range_start: datetime, range_end: datetime) -> List[Tuple[datetime, datetime, date]]:
    """
    将 [range_start, range_end] 切成按天窗口：
    - 返回 [(day_start_dt, day_end_dt, work_date), ...]
    """
    if range_end < range_start:
        return []

    tz = timezone.get_current_timezone()
    start_date = range_start.astimezone(tz).date()
    end_date = range_end.astimezone(tz).date()

    ranges: List[Tuple[datetime, datetime, date]] = []
    cur = start_date
    while cur <= end_date:
        day_start = datetime.combine(cur, time.min).replace(tzinfo=tz)
        day_end = datetime.combine(cur, time.max).replace(tzinfo=tz)

        window_start = max(range_start, day_start)
        window_end = min(range_end, day_end)

        ranges.append((window_start, window_end, cur))
        cur += timedelta(days=1)

    return ranges


def _dt_to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _get_or_init_sync_state() -> AttendanceSyncState:
    obj = AttendanceSyncState.objects.first()
    if obj:
        return obj
    return AttendanceSyncState.objects.create(
        last_success_at=None,
        default_backfill_days=30,
        safety_buffer_minutes=30,
    )


def _get_or_init_auth_config() -> AttendanceAuthConfig:
    obj = AttendanceAuthConfig.objects.first()
    if obj:
        return obj
    return AttendanceAuthConfig.objects.create()


def _map_student_no_to_user_id(student_nos: Iterable[str]) -> Dict[str, int]:
    """
    sys_user(student_no) -> id 映射
    - 不依赖具体 SysUser ORM 模型，直接走 SQL，适配你“sys_user 表存在且 student_no 唯一”的前提
    """
    s_list = [s for s in set(student_nos) if s]
    if not s_list:
        return {}

    placeholders = ",".join(["%s"] * len(s_list))
    sql = f"SELECT id, student_no FROM sys_user WHERE student_no IN ({placeholders})"
    with connection.cursor() as cursor:
        cursor.execute(sql, s_list)
        rows = cursor.fetchall()

    result: Dict[str, int] = {}
    for user_id, student_no in rows:
        result[str(student_no)] = int(user_id)
    return result


def _get_train_record_model():
    """
    获取 TrainRecord 模型（业务表）
    - 依赖 business app 已存在 TrainRecord
    """
    return apps.get_model("business", "TrainRecord")


def _compute_minutes_default(min_ms: int, max_ms: int) -> int:
    """
    默认计算规则（占位）：
    - 单日 minutes = floor((max - min)/60_000)
    - 若仅 1 条记录，则 0
    - 上限保护：不超过 24h
    后续你给出业务规则后，可替换为更精确的配对/区间扣除算法。
    """
    if max_ms <= min_ms:
        return 0
    minutes = (max_ms - min_ms) // 60000
    if minutes < 0:
        return 0
    if minutes > 24 * 60:
        return 24 * 60
    return int(minutes)


def _compute_minutes_with_intervals(checkin_times_ms: List[int]) -> Tuple[int, List[Tuple[int, int]]]:
    """
    新的时间段计算算法：贪心查找第一个距离>=30分钟的点

    算法：
    1. 从第一个打卡点开始
    2. 找到第一个距离>=30分钟的点作为终点
    3. 记录这个时间段
    4. 从终点的下一个点继续

    返回：(总分钟数, 时间段列表[(start_ms, end_ms)])
    """
    if len(checkin_times_ms) < 2:
        return 0, []

    sorted_times = sorted(checkin_times_ms)
    intervals = []
    i = 0
    MIN_INTERVAL_MS = 30 * 60 * 1000  # 30分钟

    while i < len(sorted_times):
        t_start = sorted_times[i]

        # 找到第一个距离 >= 30分钟的点
        found = False
        for j in range(i + 1, len(sorted_times)):
            if sorted_times[j] - t_start >= MIN_INTERVAL_MS:
                intervals.append((t_start, sorted_times[j]))
                i = j + 1  # 从终点的下一个点继续
                found = True
                break

        if not found:
            i += 1  # 当前点无法形成有效时间段，跳过

    # 计算总时长
    total_minutes = sum((end - start) // 60000 for start, end in intervals)
    return total_minutes, intervals


def _check_violations(work_date: date, minutes: int, intervals: List[Tuple[int, int]]) -> Tuple[int, Optional[str]]:
    """
    检查违规情况

    违规规则：
    1. 总时长 < 14小时（840分钟）
    2. 周六打卡时间段未覆盖 12:00-17:00

    返回：(违规次数, 违规原因)
    """
    violations = []

    # 违规1：总时长不足14小时
    if minutes < 840:  # 14小时 = 840分钟
        violations.append(f"总时长不足14小时（实际{minutes}分钟）")

    # 违规2：周六未覆盖 12:00-17:00
    if work_date.weekday() == 5:  # 5 = 周六
        if not intervals:
            violations.append("周六无有效训练时间段")
        else:
            # 检查是否有时间段完全覆盖 12:00-17:00
            tz = timezone.get_current_timezone()
            required_start = datetime.combine(work_date, time(12, 0)).replace(tzinfo=tz)
            required_end = datetime.combine(work_date, time(17, 0)).replace(tzinfo=tz)
            required_start_ms = int(required_start.timestamp() * 1000)
            required_end_ms = int(required_end.timestamp() * 1000)

            covered = False
            for start_ms, end_ms in intervals:
                if start_ms <= required_start_ms and end_ms >= required_end_ms:
                    covered = True
                    break

            if not covered:
                violations.append("周六训练时间段未覆盖12:00-17:00")

    violation_count = len(violations)
    violation_reason = "；".join(violations) if violations else None

    return violation_count, violation_reason


def _aggregate_daily_minutes(work_date: date) -> Dict[str, Tuple[int, int, Optional[str]]]:
    """
    对某一天，从 attendance_checkin 聚合得到 student_no -> (minutes, violation_times, violation_reason)
    - 使用新的时间段计算算法
    - 包含违规检测
    """
    tz = timezone.get_current_timezone()
    day_start = datetime.combine(work_date, time.min).replace(tzinfo=tz)
    day_end = datetime.combine(work_date, time.max).replace(tzinfo=tz)

    # 按学号分组获取所有打卡记录
    checkins_by_student = {}
    for checkin in AttendanceCheckin.objects.filter(
        check_in_time__gte=day_start, check_in_time__lte=day_end
    ).order_by("check_in_time_ms"):
        student_no = checkin.student_no
        if not student_no:
            continue
        if student_no not in checkins_by_student:
            checkins_by_student[student_no] = []
        checkins_by_student[student_no].append(checkin.check_in_time_ms)

    result: Dict[str, Tuple[int, int, Optional[str]]] = {}
    for student_no, checkin_times_ms in checkins_by_student.items():
        # 计算训练时长和时间段
        minutes, intervals = _compute_minutes_with_intervals(checkin_times_ms)

        # 检查违规
        violation_count, violation_reason = _check_violations(work_date, minutes, intervals)

        result[student_no] = (minutes, violation_count, violation_reason)

    return result


def _write_back_train_record(work_date: date, daily_data: Dict[str, Tuple[int, int, Optional[str]]], source: str = "deli") -> int:
    """
    将某一天的数据写回 train_record（按 user_id+date upsert）
    daily_data: student_no -> (minutes, violation_times, violation_reason)
    返回：成功写入（插入/更新）条数
    """
    if not daily_data:
        return 0

    student_no_to_user_id = _map_student_no_to_user_id(daily_data.keys())
    TrainRecord = _get_train_record_model()

    written = 0
    now = timezone.now()

    for student_no, (minutes, violation_times, violation_reason) in daily_data.items():
        user_id = student_no_to_user_id.get(student_no)
        if not user_id:
            # 找不到 sys_user：跳过，但不抛错，避免整批失败
            continue

        # extra 建议存可解释信息（先给最小可用）
        extra_obj = {
            "computed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "rule_version": "interval_v1",  # 更新版本号
            "student_no": student_no,
        }
        extra_str = json.dumps(extra_obj, ensure_ascii=False)

        # 依赖你已添加 UNIQUE(user_id, date) 约束（迁移已提供）
        TrainRecord.objects.update_or_create(
            user_id=user_id,
            date=work_date,
            defaults={
                "minutes": int(minutes),
                "source": source,
                "extra": extra_str,
                "update_time": now,
                "violation_times": violation_times,
                "violation_reason": violation_reason,
            },
        )
        written += 1

    return written


def _ingest_rows(rows: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    将第三方 rows 去重落库到 attendance_checkin
    返回：(inserted_count, updated_count)
    当前策略：
    - 预查询已存在 dedupe_key，准确统计 inserted
    - 已存在的记录不做更新（updated_count=0），避免无谓写放大
    """
    if not rows:
        return 0, 0

    to_create: List[AttendanceCheckin] = []
    dedupe_keys: List[str] = []

    for r in rows:
        try:
            org_id = str(r.get("org_id") or "")
            check_in_time_ms = int(r.get("check_in_time") or 0)

            extra = r.get("checkin_extra_data") or {}
            student_no = str(extra.get("employee_num") or "").strip()

            checkin_type = str(r.get("checkin_type") or "")
            source = str(r.get("source") or "")

            if not student_no or not check_in_time_ms:
                continue

            dedupe_key = build_dedupe_key(
                org_id=org_id,
                student_no=student_no,
                check_in_time_ms=check_in_time_ms,
                checkin_type=checkin_type,
                source=source,
            )
            dedupe_keys.append(dedupe_key)

            to_create.append(
                AttendanceCheckin(
                    org_id=org_id,
                    student_no=student_no,
                    check_in_time_ms=check_in_time_ms,
                    check_in_time=_to_dt_from_ms(check_in_time_ms),
                    checkin_type=checkin_type,
                    source=source,
                    device_name=str(extra.get("device_name") or "")[:200] or None,
                    raw_json=r,
                    dedupe_key=dedupe_key,
                )
            )
        except Exception:
            # 单条脏数据直接跳过
            continue

    if not to_create:
        return 0, 0

    # 批量去重统计
    existing = set(
        AttendanceCheckin.objects.filter(dedupe_key__in=dedupe_keys).values_list("dedupe_key", flat=True)
    )
    new_objs = [obj for obj in to_create if obj.dedupe_key not in existing]

    if not new_objs:
        return 0, 0

    AttendanceCheckin.objects.bulk_create(new_objs, batch_size=500)
    return len(new_objs), 0


def _require_env(name: str) -> str:
    import os

    v = os.getenv(name, "").strip()
    if not v:
        raise AttendanceClientError(f"缺少环境变量：{name}")
    return v


def run_attendance_pipeline(created_by: Optional[int] = None) -> PipelineResult:
    """
    执行全流程：
    1) 计算回补区间（上次成功到现在；无上次则 30 天）
    2) 采集第三方明细 -> attendance_checkin（去重）
    3) 对覆盖到的日期逐日计算 minutes -> upsert train_record

    说明：
    - 这里先做同步执行，后续你如果要任务化（线程/Celery），只需要把该函数放进异步执行器即可。
    """
    auth_cfg = _get_or_init_auth_config()
    sync_state = _get_or_init_sync_state()

    trust_code = decrypt_trust_code(auth_cfg.trust_code_cipher)
    if not trust_code:
        raise AttendanceClientError("未配置 trust_code，请先在后台保存 trust_code")

    now = timezone.now()

    if sync_state.last_success_at:
        range_start = sync_state.last_success_at - timedelta(minutes=sync_state.safety_buffer_minutes)
    else:
        range_start = now - timedelta(days=sync_state.default_backfill_days)

    range_end = now

    # 创建 job
    job = AttendanceSyncJob.objects.create(
        job_id=_sha256_hex(f"{now.timestamp()}|{created_by or ''}")[:32],
        status=AttendanceSyncJob.STATUS_QUEUED,
        range_start=range_start,
        range_end=range_end,
        cursor_day=None,
        cursor_page=1,
        created_by=created_by,
    )

    inserted_total = 0
    updated_total = 0
    computed_days = 0
    written_total = 0

    client = AttendanceClient()

    # 第三方固定参数（建议放 env；避免写死在代码或前端传）
    source_org_id = _require_env("DELI_SOURCE_ORG_ID")
    attendance_org_id = _require_env("DELI_ATTENDANCE_ORG_ID")
    member_id = _require_env("DELI_MEMBER_ID")

    try:
        job.status = AttendanceSyncJob.STATUS_RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at", "update_time"])

        # 1) 登录 + 换 token
        main_token = client.login_main(trust_code=trust_code)
        tokens = client.exchange_attendance_token(
            main_token=main_token,
            source_org_id=source_org_id,
            attendance_org_id=attendance_org_id,
            member_id=member_id,
        )

        # 2) 采集明细（按天切片 + 分页）
        day_windows = _day_ranges(range_start, range_end)

        for window_start, window_end, work_date in day_windows:
            job.cursor_day = work_date
            job.cursor_page = 1
            job.save(update_fields=["cursor_day", "cursor_page", "update_time"])

            start_ms = _dt_to_ms(window_start)
            end_ms = _dt_to_ms(window_end)

            # 拉全当天范围
            rows = client.fetch_records_all(
                attendance_token=tokens.attendance_token,
                source_org_id=source_org_id,
                attendance_org_id=attendance_org_id,
                member_id=member_id,
                start_time_ms=start_ms,
                end_time_ms=end_ms,
                size=100,
            )

            ins, upd = _ingest_rows(rows)
            inserted_total += ins
            updated_total += upd

        # 3) 计算并写回 train_record（对覆盖日期逐日）
        tz = timezone.get_current_timezone()
        start_date = range_start.astimezone(tz).date()
        end_date = range_end.astimezone(tz).date()

        cur = start_date
        while cur <= end_date:
            daily_minutes = _aggregate_daily_minutes(cur)
            written_total += _write_back_train_record(cur, daily_minutes, source="deli")
            computed_days += 1
            cur += timedelta(days=1)

        # 4) 全流程成功，更新水位（注意：只在全流程成功后更新）
        with transaction.atomic():
            sync_state.last_success_at = range_end
            sync_state.save(update_fields=["last_success_at", "update_time"])

            job.status = AttendanceSyncJob.STATUS_SUCCESS
            job.inserted_count = inserted_total
            job.updated_count = updated_total
            job.finished_at = timezone.now()
            job.error_code = None
            job.error_message = None
            job.save(
                update_fields=[
                    "status",
                    "inserted_count",
                    "updated_count",
                    "finished_at",
                    "error_code",
                    "error_message",
                    "update_time",
                ]
            )

        # 更新鉴权状态
        auth_cfg.last_verified_at = timezone.now()
        auth_cfg.last_error = None
        auth_cfg.save(update_fields=["last_verified_at", "last_error", "updated_at"])

        return PipelineResult(
            job_id=job.job_id,
            inserted_count=inserted_total,
            updated_count=updated_total,
            computed_days=computed_days,
            written_records=written_total,
        )

    except AttendanceClientError as e:
        job.status = AttendanceSyncJob.STATUS_FAILED
        job.error_code = "attendance_client_error"
        job.error_message = str(e)[:1000]
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_code", "error_message", "finished_at", "update_time"])

        auth_cfg.last_error = str(e)[:500]
        auth_cfg.save(update_fields=["last_error", "updated_at"])
        raise

    except Exception as e:
        job.status = AttendanceSyncJob.STATUS_FAILED
        job.error_code = "internal_error"
        job.error_message = str(e)[:1000]
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_code", "error_message", "finished_at", "update_time"])
        raise


# Django ORM annotate needs models.Min/Max; 延迟 import 以避免循环引用
from django.db import models  # noqa: E402  (placed at end intentionally)
