# attendance/urls.py
from django.urls import path

from attendance import views_admin

urlpatterns = [
    # 保存 trust_code（可选立即执行流水线）
    path("admin/trust_code", views_admin.save_trust_code),

    # 手动触发流水线（自动回补缺口）
    path("admin/pipeline/run", views_admin.run_pipeline),

    # 查询流水线状态（水位 + 最近任务）
    path("admin/pipeline/state", views_admin.pipeline_state),

    # 任务列表/详情
    path("admin/pipeline/jobs", views_admin.jobs),
    path("admin/pipeline/jobs/<str:job_id>", views_admin.job_detail),
]
