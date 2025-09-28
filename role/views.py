from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from role.models import SysRole


# Create your views here.
# 查询所有角色信息
class ListAllView(View):
    def get(self, request):
        obj_roleList = SysRole.objects.all().values()  # 转成字典
        roleList = list(obj_roleList)  # 把外层的容器转为List
        return JsonResponse({'code': 200, 'roleList': roleList})
