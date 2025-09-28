from django.urls import path
from role.views import ListAllView

urlpatterns = [
    path('listAll', ListAllView.as_view(), name='listAll'),  # 查询所有角色信息
]