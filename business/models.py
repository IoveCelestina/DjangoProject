from django.db import models

from django.db import models

class TrainRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)           # 对应 sys_user.id
    date = models.DateField(db_index=True)                 # 训练日期
    minutes = models.IntegerField()                        # 当天训练总分钟数
    source = models.CharField(max_length=20, default='manual')  # manual/deli
    extra = models.JSONField(null=True, blank=True)        # 预留原始数据
    violation_times = models.IntegerField(default=0)  # 违规次数
    violation_reason = models.TextField(null=True, blank=True)  # 违规原因（较长建议 TextField）
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'train_record'
        indexes = [
            models.Index(fields=['user_id', 'date']),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user_id", "date"], name="uniq_train_record_user_date")
        ]
class LeaveRequest(models.Model):
    """
    请假申请记录（带日期区间）
    """
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)                  # 对应 sys_user.id
    start_date = models.DateField(db_index=True)                  # 请假开始日期
    end_date = models.DateField(db_index=True)                    # 请假结束日期
    status = models.CharField(max_length=20, default='pending')   # pending/approved/rejected/cancelled
    reason = models.CharField(max_length=500, null=True, blank=True)         # 请假理由，可为空
    admin_comment = models.CharField(max_length=500, null=True, blank=True)  # 管理员审批意见，可为空
    create_time = models.DateTimeField(auto_now_add=True)         # 申请提交时间
    update_time = models.DateTimeField(auto_now=True)             # 最近更新时间
    decision_time = models.DateTimeField(null=True, blank=True)   # 管理员审批时间
    cancel_time = models.DateTimeField(null=True, blank=True)     # 用户取消时间

    class Meta:
        db_table = 'leave_request'
        indexes = [
            models.Index(fields=['user_id', 'start_date']),
            models.Index(fields=['status', 'start_date']),
        ]