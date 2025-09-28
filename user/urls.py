from django.urls import path

from user.views import TestView, JwtTestView, LoginView, SaveView, PwdView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),  # 登录
    path('save', SaveView.as_view(), name='save'),  # 用户信息修改
    path('test', TestView.as_view(), name='test'),  # 测试
    path('jwt_test', JwtTestView.as_view(), name='jwt_test'),  # jwt测试
    path('updateUserPwd', PwdView.as_view(), name='updateUserPwd'),  # 修改密码
]
