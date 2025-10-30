import json,base64,io,os
from base64 import b64decode
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.settings import api_settings

from DjangoProject import settings
from menu.models import SysMenu, SysMenuSerializer
from role.models import SysRole, SysUserRole
from user.models import SysUser, SysUserSerializer,CaptchaChallenge
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto import Random




# @method_decorator(csrf_exempt, name='dispatch')
# class LoginView(View):
#
#     def buildTreeMenu(selfself,sysMenuList):
#         resultMenuList:list[SysMenu]=list()
#         for menu in sysMenuList:
#             #寻找子节点
#             for e in sysMenuList:
#                 if e.parent_id==menu.id:
#                     if not hasattr(menu,"children"):
#                         menu.children=list()
#                     menu.children.append(e)
#             #判读那父节点，添加到集合
#             if menu.parent_id==0:
#                 resultMenuList.append(menu)
#
#         return resultMenuList
#
#     def post(self, request):
#         # === 先拿到前端传来的字段 ===
#         username = request.GET.get("username")
#         password = request.GET.get("password")
#         challenge_id = request.GET.get("challenge_id")     # 新增
#         captcha_answer = request.GET.get("captcha_answer") # 新增
#
#         # === 第一步：校验验证码 ===
#         # 1. challenge_id / captcha_answer 是否齐全
#         if not challenge_id or not captcha_answer:
#             return JsonResponse({'code': 500, 'info': '验证码缺失！'})
#
#         # 2. challenge_id 是否存在
#         try:
#             challenge_obj = CaptchaChallenge.objects.get(id=challenge_id)
#         except CaptchaChallenge.DoesNotExist:
#             return JsonResponse({'code': 500, 'info': '验证码无效或已过期！'})
#
#         # 3. 是否过期
#         if challenge_obj.expires_at < timezone.now():
#             # 过期直接删掉
#             challenge_obj.delete()
#             return JsonResponse({'code': 500, 'info': '验证码已过期！'})
#
#         # 4. 比对答案（不区分大小写，和 zzyCaptcha 一样会把输入转成大写比较）:contentReference[oaicite:12]{index=12}
#         real_text = challenge_obj.text
#         # 验证码是一次性的，用完就删，模仿 zzyCaptcha 在验证后立刻删掉 challenge 记录的做法:contentReference[oaicite:13]{index=13}
#         challenge_obj.delete()
#
#         if captcha_answer.upper().strip() != real_text:
#             return JsonResponse({'code': 500, 'info': '验证码错误！'})
#
#         # === 第二步：账号密码校验（原逻辑） ===
#         try:
#             user = SysUser.objects.get(username=username, password=password)
#
#             # 生成JWT
#             from rest_framework_jwt.settings import api_settings
#             jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
#             jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
#             payload = jwt_payload_handler(user)
#             token = jwt_encode_handler(payload)
#
#             # 当前用户的角色集合
#             roleList = SysRole.objects.raw(
#                 "SELECT id ,NAME FROM sys_role WHERE id IN (SELECT role_id FROM sys_user_role WHERE user_id=" + str(
#                     user.id) + ")"
#             )
#
#             # 拼 roles 字符串
#             roles=",".join([role.name for role in roleList])
#
#             # 根据角色查菜单，组装菜单树
#             menuSet:set[SysMenu] = set()
#             for row in roleList:
#                 menuList = SysMenu.objects.raw(
#                     "SELECT * FROM sys_menu WHERE id IN (SELECT menu_id FROM sys_role_menu WHERE role_id=" + str(
#                         row.id) + ")")
#                 for row2 in menuList:
#                     menuSet.add(row2)
#
#             menuList:list[SysMenu]=list(menuSet)
#             sorted_menuList=sorted(menuList) # 根据 ordernum 排序（你原来这里写的是 ordername，不过我保留原写法）
#             sysMenuList:list[SysMenu] = self.buildTreeMenu(sorted_menuList)
#
#             serializerMenuList = []
#             for sysMenu in sysMenuList:
#                 serializerMenuList.append(SysMenuSerializer(sysMenu).data)
#
#         except Exception as e:
#             print("登录失败：", e)
#             return JsonResponse({'code': 500, 'info': '用户名或者密码错误！'})
#
#         # 登录成功返回
#         return JsonResponse({
#             'code': 200,
#             'token': token,
#             'user': SysUserSerializer(user).data,
#             'info': '登录成功',
#             'roles': roles,
#             'menuList': serializerMenuList
#         })

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):

    def buildTreeMenu(self, sysMenuList):
        resultMenuList: list[SysMenu] = list()
        for menu in sysMenuList:
            for e in sysMenuList:
                if e.parent_id == menu.id:
                    if not hasattr(menu, "children"):
                        menu.children = list()
                    menu.children.append(e)
            if menu.parent_id == 0:
                resultMenuList.append(menu)
        return resultMenuList

    # 加载后端私钥
    def load_rsa_private_key(self):
        # 后端私钥建议放在项目根目录 /rsa_keys/private.pem
        key_path = os.path.join(settings.BASE_DIR, "rsa_keys", "private.pem")
        with open(key_path, "rb") as f:
            private_key = RSA.import_key(f.read())
        return private_key

    # 用和前端 jsencrypt 一样的 PKCS1 v1.5 解密
    def rsa_decrypt(self, enc_text: str) -> str:
        private_key = self.load_rsa_private_key()
        cipher = PKCS1_v1_5.new(private_key)
        enc_bytes = b64decode(enc_text)
        sentinel = Random.new().read(15)
        plain_bytes = cipher.decrypt(enc_bytes, sentinel)
        return plain_bytes.decode("utf-8")

    def post(self, request):
        # 1. 接收 JSON
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({'code': 500, 'info': '请求体不是合法JSON'})

        username = data.get("username")
        enc_password = data.get("password")       # 前端传的是加密后的
        challenge_id = data.get("challenge_id")
        captcha_answer = data.get("captcha_answer")

        # 2. 校验验证码
        if not challenge_id or not captcha_answer:
            return JsonResponse({'code': 500, 'info': '验证码缺失！'})

        try:
            challenge_obj = CaptchaChallenge.objects.get(id=challenge_id)
        except CaptchaChallenge.DoesNotExist:
            return JsonResponse({'code': 500, 'info': '验证码无效或已过期！'})

        if challenge_obj.expires_at < timezone.now():
            challenge_obj.delete()
            return JsonResponse({'code': 500, 'info': '验证码已过期！'})

        real_text = challenge_obj.text
        challenge_obj.delete()

        if captcha_answer.upper().strip() != real_text:
            return JsonResponse({'code': 500, 'info': '验证码错误！'})

        # 3. 解密密码
        try:
            password = self.rsa_decrypt(enc_password)
        except Exception as e:
            print("RSA解密失败:", e)
            return JsonResponse({'code': 500, 'info': '密码解密失败！'})

        # 4. 账号密码校验（保持你原来的逻辑）
        try:
            user = SysUser.objects.get(username=username, password=password)

            from rest_framework_jwt.settings import api_settings
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            roleList = SysRole.objects.raw(
                "SELECT id ,NAME FROM sys_role WHERE id IN (SELECT role_id FROM sys_user_role WHERE user_id=" + str(
                    user.id) + ")"
            )

            roles = ",".join([role.name for role in roleList])

            menuSet: set[SysMenu] = set()
            for row in roleList:
                menuList = SysMenu.objects.raw(
                    "SELECT * FROM sys_menu WHERE id IN (SELECT menu_id FROM sys_role_menu WHERE role_id=" + str(
                        row.id) + ")")
                for row2 in menuList:
                    menuSet.add(row2)

            menuList: list[SysMenu] = list(menuSet)
            sorted_menuList = sorted(menuList)
            sysMenuList: list[SysMenu] = self.buildTreeMenu(sorted_menuList)

            serializerMenuList = []
            for sysMenu in sysMenuList:
                serializerMenuList.append(SysMenuSerializer(sysMenu).data)

        except Exception as e:
            print("登录失败：", e)
            return JsonResponse({'code': 500, 'info': '用户名或者密码错误！'})

        # 5. 返回
        return JsonResponse({
            'code': 200,
            'token': token,
            'user': SysUserSerializer(user).data,
            'info': '登录成功',
            'roles': roles,
            'menuList': serializerMenuList
        })


# Create your views here.
class TestView(View):

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if token != None and token != '':
            userList_obj = SysUser.objects.all()
            print(userList_obj, type(userList_obj))
            userList_dict = userList_obj.values()  # 转存字典
            print(userList_dict, type(userList_dict))
            userList = list(userList_dict)  # 把外层的容器转存List
            print(userList, type(userList))
            return JsonResponse({'code': 200, 'info': '测试！', 'data': userList})
        else:
            return JsonResponse({'code': 401, 'info': '没有访问权限！'})


class JwtTestView(View):

    def get(self, request):
        user = SysUser.objects.get(username='python222', password='123456')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        # 将用户对象传递进去，获取到该对象的属性值
        payload = jwt_payload_handler(user)
        # 将属性值编码成jwt格式的字符串
        token = jwt_encode_handler(payload)
        return JsonResponse({'code': 200, 'token': token})

class SaveView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        if data['id'] == -1:  # 添加
            obj_sysUser = SysUser(username=data['username'], password=data['password'],
                                  email=data['email'], phonenumber=data['phonenumber'],
                                  status=data['status'],
                                  remark=data['remark'])
            obj_sysUser.create_time = datetime.now().date()
            obj_sysUser.avatar = 'default.jpg'
            obj_sysUser.password = "123456"
            obj_sysUser.save()
        else:  # 修改
            obj_sysUser = SysUser(id=data['id'], username=data['username'], password=data['password'],
                                  avatar=data['avatar'], email=data['email'], phonenumber=data['phonenumber'],
                                  login_date=data['login_date'], status=data['status'], create_time=data['create_time'],
                                  update_time=data['update_time'], remark=data['remark'])
            obj_sysUser.update_time = datetime.now().date()
            obj_sysUser.save()
        return JsonResponse({'code': 200})

class ActionView(View):

    def get(self, request):
        """
        根据id获取用户信息
        :param request:
        :return:
        """
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        return JsonResponse({'code': 200, 'user': SysUserSerializer(user_object).data})

    def delete(self, request):
        """
       删除操作
       :param request:
        :return:
        """
        idList = json.loads(request.body.decode("utf-8"))
        SysUserRole.objects.filter(user_id__in=idList).delete()
        SysUser.objects.filter(id__in=idList).delete()
        return JsonResponse({'code': 200})

class CheckView(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        username = data['username']
        print("username=", username)
        if SysUser.objects.filter(username=username).exists():
            return JsonResponse({'code': 500})
        else:
            return JsonResponse({'code': 200})

class PwdView(View): #不安全，之后需要在前端进行加密
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        oldPassword = data['oldPassword']
        newPassword = data['newPassword']
        obj_user = SysUser.objects.get(id=id)
        if obj_user.password == oldPassword:
            obj_user.password = newPassword
            obj_user.update_time = datetime.now().date()
            obj_user.save()
            return JsonResponse({'code': 200})
        else:
            return JsonResponse({'code': 500, 'errorInfo': '原密码错误！'})


class ImageView(View):
    def post(self, request):
        file = request.FILES.get('avatar')
        print("file:", file)
        if file:
            file_name = file.name
            suffixName = file_name[file_name.rfind("."):]
            new_file_name = datetime.now().strftime('%Y%m%d%H%M%S') + suffixName
            file_path = str(settings.MEDIA_ROOT) + "\\userAvatar\\" + new_file_name
            print("file_path:", file_path)
            try:
                with open(file_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                return JsonResponse({'code': 200, 'title': new_file_name})
            except:
                return JsonResponse({'code': 500, 'errorInfo': '上传头像失败'})

class AvatarView(View):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        avatar = data['avatar']
        obj_user = SysUser.objects.get(id=id)
        obj_user.avatar = avatar
        obj_user.save()
        return JsonResponse({'code': 200})

class SearchView(View):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        pageNum = data['pageNum']  # 当前页
        pageSize = data['pageSize']  # 每页大小
        query = data['query'] #查询参数
        print(pageNum, pageSize)
        userListPage = Paginator(SysUser.objects.filter(username__icontains=query), pageSize).page(pageNum)
        print(userListPage)
        obj_users = userListPage.object_list.values()  # 转成字典
        users = list(obj_users)  # 把外层的容器转为List
        for user in users:
            userId = user['id']
            roleList=SysRole.objects.raw(
                "select id,name from sys_role where id in (select role_id from sys_user_role where user_id="+str(userId)+")"
            )
            roleListDict=[]
            for role in roleList:
                roleDict={}
                roleDict['id'] = role.id
                roleDict['name']=role.name
                roleListDict.append(roleDict)
            user['roleList']=roleListDict
        total = SysUser.objects.count()
        return JsonResponse({'code': 200, 'userList': users, 'total': total})


# 重置密码
class PasswordView(View):
    def get(self, request):
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        user_object.password = "123456"
        user_object.update_time = datetime.now().date()
        user_object.save()
        return JsonResponse({'code': 200})
# 用户状态修改
class StatusView(View):
        def post(self, request):
            data = json.loads(request.body.decode("utf-8"))
            id = data['id']
            status = data['status']
            user_object = SysUser.objects.get(id=id)
            user_object.status = status
            user_object.save()
            return JsonResponse({'code': 200})


# 用户角色授权
class GrantRole(View):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        user_id = data['id']
        roleIdList = data['roleIds']
        print(user_id, roleIdList)
        SysUserRole.objects.filter(user_id=user_id).delete()  # 删除用户角色关联表中的指定用户数据
        for roleId in roleIdList:
            userRole = SysUserRole(user_id=user_id, role_id=roleId)
            userRole.save()
        return JsonResponse({'code': 200})


class RegisterView(View):
    #创建用户+分配角色+绑定得力工号(学号)
    def post(self,request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            phonenumber = data.get("phonenumber")
            student_no = data.get("student_no")
            role_id = data.get("role_id") #角色id 默认为正式队员
            member_id = data.get("member_id")
            #校验是否重复
            if SysUser.objects.filter(username=username).exists():
                return JsonResponse({"code":400,"msg":"用户名已存在"})
            if student_no and SysUser.objects.filter(student_no=student_no).exists():
                return JsonResponse({'code':400,"msg":"学号/工号已存在"})

            #创建用户

            user = SysUser(
                username=username,
                password=password,
                email=email,
                phonenumber=phonenumber,
                student_no=student_no,
                status=1,
                create_time=datetime.now().date(),
                remark="正式队员"
            )
            user.save()
            #好像不需要member_id 与 成员之间的映射，直接查询employee_num 即可
            if role_id:
                SysUserRole.objects.create(user_id=user.id, role_id=20250001) #全部是正式队员
            else:
                #默认为正式队员
                default_role = SysRole.objects.fliter(name="正式队员").first
                if default_role:
                    SysUserRole.objects.create(user_id=user.id, role_id=default_role)

            return JsonResponse({"code":200,"msg":"注册成功","user_id":user.id})
        except Exception as e:
            print("注册异常: ",e)
            return JsonResponse({"code":500,"msg":f"注册失败:{str(e)}"})

# ===================== 下面是验证码GIF生成的工具函数 BEGIN =====================

# 和 zzyCaptcha 保持一致的参数（可以按需微调宽高）
WIDTH = 600        # 原来320 -> 翻倍
HEIGHT = 240      # 原来120 -> 翻倍
CHANNELS = 3
LOOP_FRAMES = 30 #帧率
SCROLL_SPEED = 2
FONT_SIZE = 150     # 原来75 -> 翻倍，文字会非常粗大
FONT_PATH = os.path.join(
    settings.BASE_DIR,
    "captcha_font",
    "MonaspaceNeon-WideBold.otf"
)


def _create_text_mask(text, font_size, offset):
    """
    把验证码文字画到一张灰度图上，然后转成 bool mask
    True 的位置表示要显示文字噪声，False 显示背景噪声
    """
    import numpy as _np
    mask = _np.zeros((HEIGHT, WIDTH), dtype=bool)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    img = Image.new('L', (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    # offset 类似 (15, 22)，来自 zzyCaptcha 源码:contentReference[oaicite:8]{index=8}
    draw.text(offset, text, font=font, fill=255)

    text_layer = np.array(img)
    mask[text_layer > 128] = True
    return mask


def _generate_looping_noise(width, height, channels):
    """
    生成上下滚动的黑白噪声，帧之间通过平移实现“流动”效果
    """
    noise = np.random.choice([0, 255], size=(height, width), p=[0.5, 0.5]).astype(np.uint8)
    # 复制到RGB三个通道
    return np.stack([noise] * channels, axis=-1)


def _generate_frame(frame_index, text_mask, noise_texture):
    """
    根据当前帧，把"文字区域"和"背景区域"分别从不同平移方向的噪声里取像素
    和原项目一致：文字向下滚动，背景向上滚动（视觉暂留效果）:contentReference[oaicite:9]{index=9}
    """
    frame = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
    noise_height = noise_texture.shape[0]

    y_coords = np.arange(HEIGHT).reshape(-1, 1)
    x_coords = np.arange(WIDTH).reshape(1, -1)

    text_offset = (frame_index * SCROLL_SPEED)
    bg_offset   = -(frame_index * SCROLL_SPEED)

    text_noise_y = (y_coords + text_offset) % noise_height
    bg_noise_y   = (y_coords + bg_offset) % noise_height

    text_pixels = noise_texture[text_noise_y, x_coords]
    bg_pixels   = noise_texture[bg_noise_y, x_coords]

    frame[text_mask]  = text_pixels[text_mask]
    frame[~text_mask] = bg_pixels[~text_mask]

    return frame


def generate_captcha_gif(text):
    """
    入口函数：给定验证码字符串，生成一段循环GIF字节流
    """
    text_mask = _create_text_mask(text, FONT_SIZE, (10, 44)) #往右/往下多少像素
    noise_height = LOOP_FRAMES * SCROLL_SPEED
    noise_texture = _generate_looping_noise(WIDTH, noise_height, CHANNELS)

    frames = [
        Image.fromarray(_generate_frame(i, text_mask, noise_texture))
        for i in range(LOOP_FRAMES)
    ]

    gif_bytes = io.BytesIO()
    frames[0].save(
        gif_bytes,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=40,  # 每帧约40ms
        loop=0        # 无限循环
    )

    return gif_bytes.getvalue()

# ===================== 验证码GIF生成 END =====================


def cleanup_expired_captcha():
    """
    清理过期验证码（跟 zzyCaptcha 里 cleanup_expired_challenges 的思路一样）:contentReference[oaicite:10]{index=10}
    """
    CaptchaChallenge.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

@method_decorator(csrf_exempt, name='dispatch')
class CaptchaInitView(View):
    """
    GET /user/captcha/init
    返回:
    {
        code:200,
        challenge_id:"xxxxxxxx-xxxx-....",
        img:"data:image/gif;base64,......",
        expire_sec:300
    }
    """
    def get(self, request):
        # 1. 清理一下过期的验证码
        cleanup_expired_captcha()

        # 2. 生成新的 challenge
        challenge = CaptchaChallenge.create_new()

        # 3. 生成对应的GIF
        gif_bytes = generate_captcha_gif(challenge.text)
        b64 = base64.b64encode(gif_bytes).decode('ascii')

        return JsonResponse({
            'code': 200,
            'challenge_id': str(challenge.id),
            'img': 'data:image/gif;base64,' + b64,
            'expire_sec': 300
        })
