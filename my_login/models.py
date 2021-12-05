from django.db import models
from django.contrib.auth.models import Group, User


class RegisterGroup(models.Model):
    group = models.ForeignKey(Group, models.CASCADE, verbose_name="组")

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = verbose_name_plural = "可注册的组"


class Register(models.Model):
    username = models.CharField(max_length=150, verbose_name="用户名")
    password = models.CharField(max_length=150, verbose_name="密码")
    email = models.EmailField()
    invitation_code = models.TextField(unique=True, verbose_name="邀请码")
    group = models.ForeignKey(Group, models.CASCADE, verbose_name="组")

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = verbose_name_plural = "注册"
