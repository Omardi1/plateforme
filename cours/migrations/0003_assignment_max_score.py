# Generated by Django 5.1.7 on 2025-03-15 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0002_lessoncompletion'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='max_score',
            field=models.IntegerField(default=100),
        ),
    ]
