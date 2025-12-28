from django.db import models


class AttendanceAuthConfig(models.Model):
    """
    第三方考勤鉴权配置（仅管理员维护）
    - trust_code 必须密文存储（cipher），不要存明文
    - mobile/password 建议放服务端环境变量/密钥管理，不入库
    """
    id = models.BigAutoField(primary_key=True)

    # 加密后的 trust_code（密文）
    trust_code_cipher = models.TextField(null=True, blank=True)

    # 最近一次验证通过时间/最近一次错误摘要（用于后台提示）
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=500, null=True, blank=True)

    # 审计字段
    updated_by = models.IntegerField(null=True, blank=True)  # 对应 sys_user.id（管理员）
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_auth_config"


class AttendanceSyncState(models.Model):
    """
    同步水位（用于自动回补缺口）
    """
    id = models.BigAutoField(primary_key=True)

    # 全流程（采集+计算+回写）成功时更新
    last_success_at = models.DateTimeField(null=True, blank=True)

    # 默认回补天数：没有 last_success_at 时使用
    default_backfill_days = models.IntegerField(default=30)

    # 安全缓冲：从 last_success_at 往前回补 N 分钟，避免边界漏数据（配合明细去重不会重复）
    safety_buffer_minutes = models.IntegerField(default=30)

    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_sync_state"


class AttendanceSyncJob(models.Model):
    """
    同步任务（断点续跑/排障）
    """
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_PARTIAL = "partial"

    STATUS_CHOICES = (
        (STATUS_QUEUED, "queued"),
        (STATUS_RUNNING, "running"),
        (STATUS_SUCCESS, "success"),
        (STATUS_FAILED, "failed"),
        (STATUS_PARTIAL, "partial"),
    )

    id = models.BigAutoField(primary_key=True)
    job_id = models.CharField(max_length=64, unique=True, db_index=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)

    range_start = models.DateTimeField(null=True, blank=True)
    range_end = models.DateTimeField(null=True, blank=True)

    # 断点：按天切片 + 分页
    cursor_day = models.DateField(null=True, blank=True)
    cursor_page = models.IntegerField(default=1)

    inserted_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)

    error_code = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.CharField(max_length=1000, null=True, blank=True)

    created_by = models.IntegerField(null=True, blank=True)  # 对应 sys_user.id（管理员触发）
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_sync_job"
        indexes = [
            models.Index(fields=["status", "create_time"]),
            models.Index(fields=["range_start", "range_end"]),
        ]


class AttendanceCheckin(models.Model):
    """
    第三方考勤原始明细落库表（用于去重、回补、重算）
    student_no = 第三方 employee_num，用于映射 sys_user.student_no
    """
    id = models.BigAutoField(primary_key=True)

    org_id = models.CharField(max_length=50, null=True, blank=True)
    student_no = models.CharField(max_length=50, db_index=True)  # employee_num -> sys_user.student_no

    # 原始毫秒时间戳 + 可查询的 datetime
    check_in_time_ms = models.BigIntegerField(db_index=True)
    check_in_time = models.DateTimeField(db_index=True)

    checkin_type = models.CharField(max_length=50, null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    device_name = models.CharField(max_length=200, null=True, blank=True)

    # 整条 row 原样存档（便于字段变更与排障）
    raw_json = models.JSONField(null=True, blank=True)

    # 去重指纹（宽松但必须绝不重复）
    dedupe_key = models.CharField(max_length=64, unique=True)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_checkin"
        indexes = [
            models.Index(fields=["student_no", "check_in_time"]),
            models.Index(fields=["check_in_time"]),
        ]
