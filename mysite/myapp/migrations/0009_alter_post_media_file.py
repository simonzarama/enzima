# Generated by Django 4.2.6 on 2023-10-21 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_post_media_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='media_file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/'),
        ),
    ]
