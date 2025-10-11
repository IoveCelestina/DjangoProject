from django.db import models

from django.db import models

class TrainRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)           # 对应 sys_user.id
    date = models.DateField(db_index=True)                 # 训练日期
    minutes = models.IntegerField()                        # 当天训练总分钟数
    source = models.CharField(max_length=20, default='manual')  # manual/deli
    extra = models.JSONField(null=True, blank=True)        # 预留原始数据
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'train_record'
        indexes = [
            models.Index(fields=['user_id', 'date']),
        ]
