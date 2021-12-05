import django.db.utils
from django import forms
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ratelimit.decorators import ratelimit
from django.db.utils import IntegrityError
import json
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.utils import formataddr

from .models import *

for password_validator in settings.AUTH_PASSWORD_VALIDATORS:
    if password_validator['NAME'] == 'django.contrib.auth.password_validation.MinimumLengthValidator' and \
            'OPTIONS' in password_validator.keys() and \
            'min_length' in password_validator['OPTIONS'].keys():
        min_password_value = password_validator['OPTIONS']['min_length']
        break
else:
    min_password_value = 8


class LoginSheet(forms.Form):
    username = forms.CharField(max_length=64, required=True, label="用户名",
                               widget=forms.TextInput({"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput({"class": "form-control"}),
                               max_length=64, required=True, label="密码")


def view_login(req):
    return render(req, "my_login/login_form.html", context={"LoginSheet": LoginSheet()})


@require_POST
@csrf_exempt
def add_login(req):
    sheet1 = LoginSheet(req.POST)
    if not sheet1.is_valid():
        return redirect('/main?message=登录入口错误.&color=danger')
    user = authenticate(req,
                        username=sheet1.cleaned_data['username'],
                        password=sheet1.cleaned_data['password'])
    if not user:
        return redirect('/main?message=用户名或密码不正确.&color=danger')
    login(req, user)
    return redirect("/main")


@login_required(login_url='/main')
def delete_login(req):
    logout(req)
    return redirect('/main')


class RegisterSheet(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput({"class": "form-control"}),
        label="用户名", max_length=150,
        help_text="1-150个英文字符或数字.",
    )
    password = forms.CharField(
        widget=forms.PasswordInput({"class": "form-control"}),
        label="密码",
        min_length=min_password_value, max_length=150,
        help_text=f"{min_password_value}-150个英文字符或数字.",
    )
    password_again = forms.CharField(
        widget=forms.PasswordInput({"class": "form-control"}),
        label="密码(第二次输入)",
        min_length=min_password_value, max_length=150,
    )
    email = forms.EmailField(
        widget=forms.EmailInput({"class": "form-control"}),
    )
    try:
        group = forms.ModelChoiceField(
            RegisterGroup.objects.all(), initial=RegisterGroup.objects.first(),
            widget=forms.Select({"class": "form-select"}), empty_label=None, label="组")
    except django.db.utils.OperationalError:
        pass


def view_register(req):
    context = {
        'RegisterSheet': RegisterSheet(),
    }
    return render(req, "my_login/register.html", context)


with open('token/smtp.json', "r") as f:
    config = json.load(f)


class InvitationCode(forms.Form):
    invitation_code = forms.CharField(
        widget=forms.Textarea({'class': 'form-control', 'height': 5}),
        label='注册邀请码',
        help_text='注册邀请码包含在刚才发送的邮件中.'
    )


@csrf_exempt
@require_POST
@ratelimit(key='header:x-real-ip', rate='70/10m', block=True)
@ratelimit(key='post:username', rate='2/1m', block=True)
@ratelimit(key='post:email', rate='1/1m', block=True)
def add_register(req):
    register_sheet = RegisterSheet(req.POST)
    if not register_sheet.is_valid():
        return redirect('/my_login/register?message=提交入口错误.&color=danger')
    if not register_sheet.cleaned_data['password'] == register_sheet.cleaned_data['password_again']:
        return redirect('/my_login/register?message=两次输入的密码不一致.&color=danger')
    invitation_code = ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits, k=64))
    receiver = register_sheet.cleaned_data['email']
    try:
        msg = render(req, 'my_login/email.html', {'invitation_code': invitation_code}).content.decode('utf-8')
        msg = MIMEText(msg, 'html', 'utf-8')
        msg['From'] = formataddr(('Clixove', config['username']))
        msg['To'] = formataddr((receiver, receiver))
        msg['Subject'] = 'Clixove Registration'
        server = smtplib.SMTP_SSL(config['host'], config['port'])
        server.login(config['username'], config['password'])
        server.sendmail(config['username'], [receiver], msg.as_string())
        server.quit()
    except Exception as e:
        return redirect(f'/my_login/register?message={e}&color=warning')
    if User.objects.filter(username=register_sheet.cleaned_data['username']).exists():
        return redirect('/my_login/register?message=用户已存在.&color=danger')
    new_register = Register(
        username=register_sheet.cleaned_data['username'],
        password=register_sheet.cleaned_data['password'],
        email=register_sheet.cleaned_data['email'],
        invitation_code=invitation_code,
        group=register_sheet.cleaned_data['group'].group,
    )
    new_register.save()
    return render(req, 'my_login/register_confirm.html', {'invitation_code_sheet': InvitationCode()})


@csrf_exempt
@require_POST
def add_user(req):
    invitation_code = InvitationCode(req.POST)
    if not invitation_code.is_valid():
        return redirect('/my_login/confirm?message=提交入口错误.&color=danger')
    try:
        application = Register.objects.get(invitation_code=invitation_code.cleaned_data['invitation_code'])
    except Register.DoesNotExist:
        return redirect('/my_login/confirm?message=邀请码不正确.&color=warning')
    if User.objects.filter(username=application.username).exists():
        application.delete()
        return redirect('/my_login/register?message=保留的用户名已过期.&color=danger')
    new_user = User(username=application.username, email=application.email)
    new_user.set_password(application.password)
    new_user.save()
    new_user.groups.add(application.group)
    application.delete()
    return redirect('/main?message=成功注册.&color=success')
