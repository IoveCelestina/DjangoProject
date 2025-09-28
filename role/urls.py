from django.urls import path
from role.views import ListAllView, SearchView

urlpatterns = [
    path('listAll', ListAllView.as_view(), name='listAll'),  # 查询所有角色信息
    path('search', SearchView.as_view(), name='search'),  # 角色信息查询
]