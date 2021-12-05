import io
import pickle

import numpy as np
import pandas as pd
from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from BHT_ARIMA import BHTARIMA
from task_manager.models import *
from task_manager.views import ChooseTask
from .models import *


class ConfigBhtArima(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    p = forms.IntegerField(
        widget=forms.NumberInput({'class': 'form-control'}),
        min_value=1, label='ARIMA模型-历史项数',
    )
    d = forms.IntegerField(
        widget=forms.NumberInput({'class': 'form-control'}),
        min_value=0, label='ARIMA模型-差分的阶数',
    )
    q = forms.IntegerField(
        widget=forms.NumberInput({'class': 'form-control'}),
        min_value=1, label='ARIMA模型-移动平均的长度',
    )
    tau = forms.IntegerField(
        widget=forms.NumberInput({'class': 'form-control'}),
        min_value=1, label='MDT过程-时间滞后参数',
    )

    def link_to_task(self, task):
        self.fields['task'].initial = task


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_bht_arima(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    config_sheet = ConfigBhtArima()
    config_sheet.link_to_task(task)
    context = {
        'task': task, 'config_sheet': config_sheet,
    }
    task.current_step = 3
    task.save()
    return render(req, 'BHT_ARIMA/bht_config.html', context)


@csrf_exempt
@require_POST
@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
def add_bht_arima(req):
    config_sheet = ConfigBhtArima(req.POST)
    if not config_sheet.is_valid():
        return HttpResponse('/task/list?color=danger&message=提交入口错误.')
    task = config_sheet.cleaned_data['task']
    if task.user != req.user:
        return HttpResponse('/task/list?color=warning&message=任务不存在.')

    config_sheet.link_to_task(task)
    if not config_sheet.is_valid():
        return HttpResponse(f'/task/add-3?index={task.id}&color=danger&message=提交入口错误.')
    if task.busy:
        return HttpResponse(f'/task/add-3?index={task.id}&color=warning&message=任务繁忙, 不能启动该操作.')
    task.busy = True
    task.save()

    try:
        evaluation = pd.read_pickle(task.dearesults.evaluation.path)
        prediction = pd.DataFrame(columns=['名称', '统计起止时间', '预测时间', '预测绩效', '备注'])
        for name_prov, df_prov in evaluation.groupby('province'):
            memo = []
            year_begin, year_end = df_prov.year.min(), df_prov.year.max()
            ts_length = year_end - year_begin + 1
            if df_prov.shape[0] != ts_length:
                year_index = np.linspace(year_begin, year_end, ts_length, dtype=np.int_)
                efficient_interpolated = np.interp(year_index, df_prov.year, df_prov.efficient)
                memo.append('应用插值处理时间不连续的数据')
            else:
                efficient_interpolated = df_prov.efficient
            if ts_length + 1 - config_sheet.cleaned_data['tau'] \
                    - config_sheet.cleaned_data['d'] - config_sheet.cleaned_data['p'] \
                    - config_sheet.cleaned_data['q'] <= 0:
                memo.append('MDT过程-时间滞后参数错误')
                prediction = prediction.append({
                    '名称': name_prov, '统计起止时间': (year_begin, year_end), '预测时间': '',
                    '预测绩效': '', '备注': '; '.join(memo)
                }, ignore_index=True)
            else:
                bht = BHTARIMA(efficient_interpolated[np.newaxis, :], p=config_sheet.cleaned_data['p'],
                               d=config_sheet.cleaned_data['d'], q=config_sheet.cleaned_data['q'],
                               taus=[1, config_sheet.cleaned_data['tau']],
                               Rs=[config_sheet.cleaned_data['tau'], config_sheet.cleaned_data['tau']],
                               K=100, tol=0.001, verbose=0, Us_mode=4)
                efficient_predicted, _ = bht.run()
                if (efficient_predicted[0, -1] > 1) or (efficient_predicted[0, -1] < 0):
                    memo.append('预测值不在合理范围内')
                prediction = prediction.append({
                    '名称': name_prov, '统计起止时间': (year_begin, year_end), '预测时间': year_end + 1,
                    '预测绩效': efficient_predicted[0, -1], '备注': '; '.join(memo)
                }, ignore_index=True)
        intermediate_file_handler = ContentFile(pickle.dumps(prediction))
    except Exception as e:
        new_error = AsyncErrorMessage(user=req.user, task=task, current_step=3, error_message=e.__str__())
        new_error.save()
        task.current_step = 3
        task.busy = False
        task.save()
        return HttpResponse(f'/task/add-3?index={task.id}&color=danger&message=运行错误. {e}')
    try:
        bht_model = BhtModel.objects.get(task=task)
        bht_model.p = config_sheet.cleaned_data['p']
        bht_model.q = config_sheet.cleaned_data['q']
        bht_model.d = config_sheet.cleaned_data['d']
        bht_model.tau = config_sheet.cleaned_data['tau']
        bht_model.save()
        bht_model.prediction.delete()
        bht_model.prediction.save(f'task_{task.id}_prediction.pkl', intermediate_file_handler)
    except BhtModel.DoesNotExist:
        bht_model = BhtModel(
            task=task, p=config_sheet.cleaned_data['p'], q=config_sheet.cleaned_data['q'],
            d=config_sheet.cleaned_data['d'], tau=config_sheet.cleaned_data['tau']
        )
        bht_model.save()
        bht_model.prediction.save(f'task_{task.id}_prediction.pkl', intermediate_file_handler)
    task.current_step = 4
    task.busy = False
    task.save()
    return HttpResponse(f'/task/add-4?index={task.id}&color=success&message=已完成绩效预测.')


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_prediction(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    try:
        prediction = pd.read_pickle(task.bhtmodel.prediction.path)
        prediction_html = prediction.to_html(classes='table table-sm table-bordered text-nowrap',
                                             justify='center', index=False, float_format=lambda x: format(x, '.4f'))
    except Exception as e:
        prediction_html = e.__str__()
    context = {
        'task': task, 'prediction': prediction_html,
    }
    return render(req, 'BHT_ARIMA/bht_results.html', context)


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def download_prediction(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    try:
        prediction = pd.read_pickle(task.bhtmodel.prediction.path)
        intermediate_file_handler = io.BytesIO()
        with pd.ExcelWriter(intermediate_file_handler) as f:
            prediction.to_excel(f, index=False)
    except Exception as e:
        return redirect(f'/task/add-4?index={task.id}&color=danger&message=下载失败. {e}')
    try:
        download_cache = DownloadCache.objects.get(task=task)
        download_cache.cached_file.delete()
        download_cache.cached_file.save(f'task_{task.id}_prediction.xlsx', intermediate_file_handler)
    except DownloadCache.DoesNotExist:
        download_cache = DownloadCache(task=task)
        download_cache.save()
        download_cache.cached_file.save(f'task_{task.id}_prediction.xlsx', intermediate_file_handler)
    return FileResponse(download_cache.cached_file)
