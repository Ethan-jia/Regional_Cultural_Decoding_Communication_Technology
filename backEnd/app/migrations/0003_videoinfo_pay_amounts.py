# Generated by Django 2.2.1 on 2022-11-25 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_videoinfo_is_del'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoinfo',
            name='pay_amounts',
            field=models.IntegerField(default=0, verbose_name='视频支付金额'),
        ),
    ]
