# Generated by Django 4.2.6 on 2023-12-23 03:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0028_alter_community_options_community_created_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                ('media_file', models.FileField(blank=True, upload_to='trials/')),
                ('published_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('include_crowdfunding', models.BooleanField(default=False)),
                ('goal', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('total_raised', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_donors', models.PositiveIntegerField(default=0)),
                ('administrators', models.ManyToManyField(blank=True, related_name='administered_trials', to=settings.AUTH_USER_MODEL)),
                ('communities', models.ManyToManyField(blank=True, to='myapp.community')),
                ('medical_supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervised_trials', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]