# Generated by Django 5.1.7 on 2025-03-15 14:11

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonCompletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completions', to='cours.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completed_lessons', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Leçon complétée',
                'verbose_name_plural': 'Leçons complétées',
                'ordering': ['-completed_at'],
                'unique_together': {('user', 'lesson')},
            },
        ),
    ]
