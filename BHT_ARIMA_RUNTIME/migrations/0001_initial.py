# Generated by Django 3.2.9 on 2021-12-05 04:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('task_manager', '0003_auto_20211205_0041'),
    ]

    operations = [
        migrations.CreateModel(
            name='BhtModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('p', models.IntegerField(default=3)),
                ('d', models.IntegerField(default=1)),
                ('q', models.IntegerField(default=2)),
                ('tau', models.IntegerField(default=5)),
                ('prediction', models.FileField(upload_to='prediction', verbose_name='预测结果')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='task_manager.task', verbose_name='任务')),
            ],
            options={
                'verbose_name': 'BHT-ARIMA 模型',
                'verbose_name_plural': 'BHT-ARIMA 模型',
            },
        ),
    ]
