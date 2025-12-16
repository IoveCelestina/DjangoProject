# business/migrations/0002_train_record_add_unique_user_date.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # 如果你的 business app 最新迁移号不是 0001_initial，请把这里改成你实际的最新迁移文件名
        ("business", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="trainrecord",
            constraint=models.UniqueConstraint(
                fields=("user_id", "date"),
                name="uniq_train_record_user_date",
            ),
        ),
        migrations.AddIndex(
            model_name="trainrecord",
            index=models.Index(
                fields=["date", "user_id"],
                name="idx_train_record_date_user",
            ),
        ),
    ]
