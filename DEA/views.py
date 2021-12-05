import json
import pickle
import io
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from task_manager.models import *
from task_manager.views import ChooseTask
from scipy.optimize import linprog
from .models import *


class VariablePicker(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    name_time = forms.ModelChoiceField(
        Column.objects.all(), widget=forms.Select({'class': 'form-select'}),
        label='年份变量',
        help_text='必须是整数. 如非年份, 需转化为整数表示的时期序号.'
    )
    name_dmu = forms.ModelChoiceField(
        Column.objects.all(), widget=forms.Select({'class': 'form-select'}),
        label='环保机构变量',
    )
    names_input = forms.ModelMultipleChoiceField(
        Column.objects.all(), widget=forms.CheckboxSelectMultiple(),
        label='投入变量'
    )
    names_output = forms.ModelMultipleChoiceField(
        Column.objects.all(), widget=forms.CheckboxSelectMultiple(),
        label='产出变量'
    )

    def load_choices(self, task):
        self.fields['names_input'].queryset = self.fields['names_output'].queryset \
            = self.fields['name_time'].queryset = self.fields['name_dmu'].queryset = task.column_set.all()
        self.fields['task'].initial = task


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_set_variables(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    set_variable_sheet = VariablePicker()
    set_variable_sheet.load_choices(task)
    context = {
        'set_variable_sheet': set_variable_sheet, 'task': task,
    }
    return render(req, 'DEA/set_variables.html', context)


@csrf_exempt
@require_POST
@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
def set_variable(req):
    set_variable_sheet = VariablePicker(req.POST)
    if not set_variable_sheet.is_valid():
        return HttpResponse('/task/list?color=danger&message=提交入口错误.')
    task = set_variable_sheet.cleaned_data['task']
    if task.user != req.user:
        return HttpResponse('/task/list?color=warning&message=任务不存在.')

    set_variable_sheet.load_choices(task)
    if not set_variable_sheet.is_valid():
        return HttpResponse(f'/task/add-1?index={task.id}&color=danger&message=提交入口错误.')
    if task.busy:
        return HttpResponse(f'/task/add-1?index={task.id}&color=warning&message=任务繁忙, 不能启动该操作.')
    task.busy = True
    task.save()

    for col in task.column_set.all():
        col.is_datetime = col == set_variable_sheet.cleaned_data['name_time']
        col.is_dmu = col == set_variable_sheet.cleaned_data['name_dmu']
        col.is_input = col in set_variable_sheet.cleaned_data['names_input']
        col.is_output = col in set_variable_sheet.cleaned_data['names_output']
        col.save()

    try:
        names_input = [col.name for col in set_variable_sheet.cleaned_data['names_input']]
        names_output = [col.name for col in set_variable_sheet.cleaned_data['names_output']]
        dmu = pd.read_pickle(task.dataset.path)
        mat_input, mat_output = dmu[names_input].values.astype('float32'), dmu[names_output].values.astype('float32')

        n = mat_output.shape[0]
        efficients = np.zeros(shape=n)
        for i in range(n):
            opt = linprog(
                c=np.hstack([-mat_output[i, :], np.zeros(shape=mat_input.shape[1])]),
                A_ub=np.hstack([mat_output, -mat_input]),
                b_ub=np.zeros(shape=n),
                A_eq=np.hstack([np.zeros(shape=(1, mat_output.shape[1])), mat_input[i:i + 1, :]]),
                b_eq=np.array([1.]),
            )
            efficients[i] = - opt.fun
        name_dmu = set_variable_sheet.cleaned_data['name_dmu'].name
        name_time = set_variable_sheet.cleaned_data['name_time'].name
        evaluation = pd.DataFrame({
            'year': dmu[name_time].astype('int32'),
            'province': dmu[name_dmu].astype('str'), 'efficient': efficients.astype('float32')
        })
        intermediate_file_handler = ContentFile(pickle.dumps(evaluation))
        dmu_list = json.dumps(evaluation['province'].unique().tolist(), ensure_ascii=False)
    except Exception as e:
        new_error = AsyncErrorMessage(user=req.user, task=task, current_step=1, error_message=e.__str__())
        new_error.save()
        task.current_step = 1
        task.busy = False
        task.save()
        return HttpResponse(f'/task/add-1?index={task.id}&color=danger&message=运行错误. {e}')
    try:
        dea = DeaResults.objects.get(task=task)
        dea.dmu_list = dmu_list
        dea.save()
        dea.evaluation.delete()
        dea.evaluation.save(f'task_{task.id}_eval.pkl', intermediate_file_handler)
    except DeaResults.DoesNotExist:
        dea = DeaResults(task=task, dmu_list=dmu_list)
        dea.save()
        dea.evaluation.save(f'task_{task.id}_eval.pkl', intermediate_file_handler)
    task.current_step = 2
    task.busy = False
    task.save()
    return HttpResponse(f'/task/add-2?index={task.id}&color=success&message=已完成绩效评价.')


class SelectDMU(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    cjk_font_support = forms.BooleanField(
        widget=forms.Select({'class': 'form-control form-select'}, choices=[(True, '是'), (False, '否')]),
        required=False, label='环境保护机构名称是否包含中日韩文字?', initial=True,
    )
    dmu = forms.ChoiceField(
        widget=forms.Select({'class': 'form-control form-select'}),
        label='选择环境保护机构',
    )

    def link_to_task(self, task):
        self.fields['task'].initial = task

    def load_choices(self, choices):
        self.fields['dmu'].choices = [(x, x) for x in choices]


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_dea_results(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    select_dmu_sheet = SelectDMU()
    select_dmu_sheet.load_choices(json.loads(task.dearesults.dmu_list))
    select_dmu_sheet.link_to_task(task)
    context = {
        'task': task, 'select_dmu_sheet': select_dmu_sheet,
    }
    return render(req, 'DEA/dea_results.html', context)


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
@csrf_exempt
@require_POST
def draw_efficients(req):
    select_dmu = SelectDMU(req.POST)
    select_dmu.is_valid()
    task = select_dmu.cleaned_data['task']
    if task.user != req.user:
        context = {'color': 'danger', 'content': '任务不存在.'}
        return render(req, 'task/hint_widget.html', context)
    select_dmu = SelectDMU(req.POST)
    select_dmu.load_choices(json.loads(task.dearesults.dmu_list))
    if not select_dmu.is_valid():
        context = {'color': 'danger', 'content': '提交入口错误.'}
        return render(req, 'task/hint_widget.html', context)

    try:
        evaluation = pd.read_pickle(task.dearesults.evaluation.path)
        f, fig = io.StringIO(), plt.figure()
        province = evaluation[evaluation['province'] == select_dmu.cleaned_data['dmu']]
        plt.plot(province.year, province.efficient)
        plt.xlabel('Year')
        plt.ylabel('Efficient')
        if select_dmu.cleaned_data['cjk_font_support']:
            plt.title(select_dmu.cleaned_data['dmu'], fontproperties=FontProperties(
                fname='SourceHanSerifCN-Regular.ttf', size=14,
            ))
        else:
            plt.title(select_dmu.cleaned_data['dmu'])
        fig.savefig(f, format='svg')
        plt.close(fig)
    except Exception as e:
        context = {'color': 'danger', 'content': f'运行错误. {e}'}
        return render(req, 'task/hint_widget.html', context)
    return HttpResponse(f.getvalue())


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def download_efficients(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    try:
        evaluation = pd.read_pickle(task.dearesults.evaluation.path)
        evaluation.columns = ['统计时间', '名称', '绩效']
        intermediate_file_handler = io.BytesIO()
        with pd.ExcelWriter(intermediate_file_handler) as f:
            evaluation.to_excel(f, index=False)
    except Exception as e:
        return redirect(f'/task/add-2?index={task.id}&color=danger&message=下载失败. {e}')
    try:
        download_cache = DownloadCache.objects.get(task=task)
        download_cache.cached_file.delete()
        download_cache.cached_file.save(f'task_{task.id}_efficients.xlsx', intermediate_file_handler)
    except DownloadCache.DoesNotExist:
        download_cache = DownloadCache(task=task)
        download_cache.save()
        download_cache.cached_file.save(f'task_{task.id}_efficients.xlsx', intermediate_file_handler)
    return FileResponse(download_cache.cached_file)
