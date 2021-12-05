import pickle

import pandas as pd
from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import *


def view_main(req):
    context = {}
    return render(req, "main.html", context)


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_tasks(req):
    context = {
        "tasks": Task.objects.filter(user=req.user),
        "errors": AsyncErrorMessage.objects.filter(user=req.user).order_by('-happened_time'),
    }
    return render(req, "task/list.html", context)


class ChooseTask(forms.Form):
    index = forms.ModelChoiceField(Task.objects.all())


@permission_required("task_manager.delete_task", login_url="/main?color=danger&message=没有删除任务的权限.")
def delete_task(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    if task.busy:
        return redirect('/task/list?color=danger&message=不能删除繁忙的任务.')
    task.delete()
    return redirect('/task/list?color=success&message=成功删除.')


class AddTask(forms.Form):
    name = forms.CharField(
        max_length=64, label='任务名称',
        widget=forms.TextInput({'class': 'form-control'}),
    )
    dataset = forms.FileField(
        label='上传数据集',
        widget=forms.FileInput({'class': 'form-control'}),
    )


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_add_task(req):
    context = {
        'add_task_form': AddTask(),
    }
    return render(req, "task/add_task.html", context)


@permission_required("task_manager.add_task", login_url="/main?color=danger&message=没有新增任务的权限.")
@require_POST
@csrf_exempt
def add_task(req):
    add_task_sheet = AddTask(req.POST, req.FILES)
    if not add_task_sheet.is_valid():
        return redirect('/task/add-1?color=danger&message=提交入口错误.')
    try:
        dataset = pd.read_excel(add_task_sheet.cleaned_data['dataset'])
        dataset.dropna()
    except Exception as e:
        return redirect(f'/task/add-1?color=danger&message=文件的格式不正确. {e}')
    new_task = Task(name=add_task_sheet.cleaned_data['name'], user=req.user)
    new_task.save()
    intermediate_file_handler = ContentFile(pickle.dumps(dataset))
    new_task.dataset.delete()
    new_task.dataset.save(f'task_{new_task.id}_dataset.pkl', intermediate_file_handler)
    for col in dataset.columns:
        new_column = Column(task=new_task, name=col)
        new_column.save()
    return redirect(f'/task/add-1?index={new_task.id}')
