# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-21 07:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recapp', '0002_auto_20170820_1441'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='name',
            field=models.CharField(default='asadasd', max_length=1000),
            preserve_default=False,
        ),
    ]
