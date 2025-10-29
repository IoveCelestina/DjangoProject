from rest_framework import serializers
import uuid
import random
from datetime import timedelta
from django.db import models
from django.utils import timezone

# Create your models here.
class SysUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=100, verbose_name="密码")
    avatar = models.CharField(max_length=255, null=True, verbose_name="用户头像")
    email = models.CharField(max_length=100, null=True, verbose_name="用户邮箱")
    phonenumber = models.CharField(max_length=11, null=True, verbose_name="手机号码")
    student_no = models.CharField(max_length=50, null=True, blank=True, unique=True)  # 新增：学号/工号（可唯一）
    login_date = models.DateField(null=True, verbose_name="最后登录时间")
    status = models.IntegerField(null=True, verbose_name="帐号状态（0正常 1停用）")
    create_time = models.DateField(null=True, verbose_name="创建时间", )
    update_time = models.DateField(null=True, verbose_name="更新时间")
    remark = models.CharField(max_length=500, null=True, verbose_name="备注")

    class Meta:
        db_table = "sys_user"


class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'


# user/models.py 里的结尾处追加


class CaptchaChallenge(models.Model):
    """
    一次验证码挑战:
    - id: 主键 UUID，前端要带回给后端
    - text: 正确答案（大写英文字母）
    - expires_at: 过期时间，默认 5 分钟
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=10)
    expires_at = models.DateTimeField()

    @classmethod
    def create_new(cls):
        """
        生成一条新的验证码挑战，模仿 zzyCaptcha：
        - 字符集不包含容易混淆的字符，比如 I / O / Q 等
        - 长度固定为 5
        - 5 分钟后过期
        """
        ALLOWED_CHARS = "ABCDEFGHJKLMNPRSTXYZ"  # 仓库里用的字符集:contentReference[oaicite:6]{index=6}
        CAPTCHA_LENGTH = 5

        text = ''.join(random.choices(ALLOWED_CHARS, k=CAPTCHA_LENGTH))
        expires_at = timezone.now() + timedelta(minutes=5)

        obj = cls.objects.create(
            text=text,
            expires_at=expires_at
        )
        return obj
