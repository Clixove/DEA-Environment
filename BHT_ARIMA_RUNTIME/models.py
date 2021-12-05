from django.db import models
from task_manager.models import Task


class BhtModel(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    p = models.IntegerField(default=3)
    d = models.IntegerField(default=1)
    q = models.IntegerField(default=2)
    tau = models.IntegerField(default=5)
    prediction = models.FileField(upload_to='prediction', verbose_name='预测结果')

    class Meta:
        verbose_name = verbose_name_plural = 'BHT-ARIMA 模型'


class DownloadCache(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务', related_name='DownloadTask1')
    cached_file = models.FileField(upload_to='download_cache', verbose_name='下载缓存')

    def __str__(self):
        return self.task.name
