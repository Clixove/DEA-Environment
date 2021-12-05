from django.db import models
from django.contrib.auth.models import User

step_names = {
    1: '01-已提交数据集',
    2: '02-已完成绩效评价',
    3: '03-配置绩效预测模型',
    4: '04-已完成绩效预测',
}


class Task(models.Model):
    name = models.CharField(max_length=64, verbose_name='名称')
    user = models.ForeignKey(User, models.CASCADE, verbose_name='用户')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    busy = models.BooleanField(default=False, verbose_name='繁忙')
    current_step = models.IntegerField(default=1, verbose_name='当前步骤')
    dataset = models.FileField(upload_to='dataset', verbose_name='数据集')

    def __str__(self):
        return self.name

    def current_step_description(self):
        if self.current_step not in step_names.keys():
            return '00-未知流程'
        return step_names[self.current_step]

    class Meta:
        verbose_name = verbose_name_plural = '任务'


class Column(models.Model):
    task = models.ForeignKey(Task, models.CASCADE, verbose_name='任务')
    name = models.TextField(verbose_name='名称')
    is_datetime = models.BooleanField(default=False, verbose_name='时间?')
    is_dmu = models.BooleanField(default=False, verbose_name='DMU?')
    is_input = models.BooleanField(default=False, verbose_name='投入?')
    is_output = models.BooleanField(default=False, verbose_name='产出?')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = '列'


class AsyncErrorMessage(models.Model):
    user = models.ForeignKey(User, models.CASCADE, verbose_name='用户')
    task = models.ForeignKey(Task, models.CASCADE, verbose_name='任务')
    happened_time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')
    current_step = models.IntegerField(verbose_name='发生在步骤')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    def __str__(self):
        return self.task.name + '-' + self.happened_time.strftime('%Y-%m-%d-%H:%M:%s')

    def current_step_description(self):
        if self.current_step not in step_names.keys():
            return '00-未知流程'
        return step_names[self.current_step]

    class Meta:
        verbose_name = verbose_name_plural = '异步错误'
