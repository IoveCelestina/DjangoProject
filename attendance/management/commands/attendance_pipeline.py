# attendance/management/commands/attendance_pipeline.py
import json
from typing import Any, Dict, Optional

from django.core.management.base import BaseCommand

from attendance.attendance_client import AttendanceClientError
from attendance.pipeline_service import run_attendance_pipeline


class Command(BaseCommand):
    """
    Django 管理命令入口：执行考勤流水线
    - 采集第三方明细 -> 去重入库 attendance_checkin
    - 按天计算 minutes -> upsert 写回 train_record (user_id, date)

    使用方式：
      python manage.py attendance_pipeline
      python manage.py attendance_pipeline --user-id 1
    """

    help = "Run attendance pipeline: ingest checkins -> compute minutes -> write back train_record."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help="Optional creator user_id for job auditing.",
        )

    def handle(self, *args, **options):
        created_by: Optional[int] = options.get("user_id")

        try:
            result = run_attendance_pipeline(created_by=created_by)
            out: Dict[str, Any] = {
                "ok": True,
                "job_id": result.job_id,
                "inserted_count": result.inserted_count,
                "updated_count": result.updated_count,
                "computed_days": result.computed_days,
                "written_records": result.written_records,
            }
            self.stdout.write(json.dumps(out, ensure_ascii=False))
        except AttendanceClientError as e:
            out = {"ok": False, "error_type": "attendance_client_error", "error": str(e)}
            self.stderr.write(json.dumps(out, ensure_ascii=False))
            raise
        except Exception as e:
            out = {"ok": False, "error_type": "internal_error", "error": str(e)}
            self.stderr.write(json.dumps(out, ensure_ascii=False))
            raise
