# business/urls.py
from django.urls import path
from .views_my import MyOverviewView, MyListView, MyLeaveAddView, MyLeaveListView, MyLeaveCancelView
from .views_admin import AdminSearchView, LeaveAdminListView, LeaveAdminApproveView

urlpatterns = [
    #训练记录相关
    path('training/my/overview', MyOverviewView.as_view()),
    path('training/my/list',     MyListView.as_view()),
    path('training/admin/search',AdminSearchView.as_view()),

    #请假-我的
    path('leave/my/add', MyLeaveAddView.as_view()),  # // <--- 新增代码
    path('leave/my/cancel', MyLeaveCancelView.as_view()),  # // <--- 新增代码
    path('leave/my/list', MyLeaveListView.as_view()),  # // <--- 新增代码

    # 请假 - 管理员
    path('leave/admin/list', LeaveAdminListView.as_view()),  # // <--- 新增代码
    path('leave/admin/approve', LeaveAdminApproveView.as_view()),  # // <--- 新增代码
]
