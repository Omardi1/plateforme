# Generated by Django 5.1.7 on 2025-03-15 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0004_remove_userprofile_github_url_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='linkedin_url',
            new_name='social_links',
        ),
    ]
