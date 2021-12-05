from django.db import models
from task_manager.models import Task


class DeaResults(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    evaluation = models.FileField(upload_to='evaluation', verbose_name='绩效评价')
    dmu_list = models.TextField(blank=True, verbose_name='环境保护机构')

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = '绩效评价结果'


class DownloadCache(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务', related_name='DownloadTask2')
    cached_file = models.FileField(upload_to='download_cache', verbose_name='下载缓存')

    def __str__(self):
        return self.task.name
