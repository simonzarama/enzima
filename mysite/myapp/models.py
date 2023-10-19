from django.db import models
from django.contrib.auth.models import User




class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    community_type = models.CharField(max_length=10, choices=[
        ('public', 'Public'),
        ('restricted', 'Restricted'),
        ('private', 'Private')
    ])

class Post(models.Model):
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title