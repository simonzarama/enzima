from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation






class Community(models.Model):
    # Campos existentes
    name = models.CharField(max_length=100, unique=True)
    community_type = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Public'),
            ('restricted', 'Restricted'),
            ('private', 'Private')
        ],
    )

    # Nuevos campos agregados
    created_at = models.DateTimeField(default=timezone.now)
    followers = models.ManyToManyField(
        'auth.User',
        related_name='followed_communities',
        blank=True  # Permite comunidades sin seguidores
    )

    def __str__(self):
        return self.name

    # Métodos adicionales para obtener la cantidad de seguidores y la fecha de creación, si se requiere
    @property
    def follower_count(self):
        return self.followers.count()

    class Meta:
        ordering = ['-created_at']  # Or


        
class Post(models.Model):
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    published_at = models.DateTimeField(default=timezone.now)
    likes_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def is_liked_by(self, user):
        return self.like_set.filter(user=user).exists()


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_likes_count()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_likes_count()

    def update_likes_count(self):
        self.post.likes_count = self.post.like_set.count()
        self.post.save()

class SavedContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Contenido {self.content_type} con ID {self.object_id} guardado por {self.user.username}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.user.username} en {self.post.title}"


class CrowdfundingCampaign(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    goal = models.DecimalField(max_digits=10, decimal_places=2)  # Meta de recaudación
    total_donations = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Monto total recaudado
    total_donors = models.PositiveIntegerField(default=0)  # Número total de donantes
    likes_count = models.IntegerField(default=0)  # Número de 'likes'
    published_at = models.DateTimeField(default=timezone.now)  # Fecha de publicación
    likers = models.ManyToManyField(User, related_name='liked_campaigns', blank=True)  # Campo ManyToMany para los 'likers'
    communities = models.ManyToManyField(Community, blank=True)  # Comunidades asociadas
    media_file = models.FileField(upload_to='campaigns/')  # Archivo multimedia asociado
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Creador de la campaña
    saved_contents = GenericRelation(SavedContent)  # Contenidos guardados asociados

    # ... otros campos ...

    def is_liked_by(self, user):
        """
        Verifica si un usuario ha dado 'like' a la campaña.
        :param user: User instance.
        :return: Boolean indicating whether the user liked the campaign.
        """
        return self.likers.filter(id=user.id).exists()

    def get_absolute_url(self):
        """
        Devuelve la URL absoluta para una instancia de campaña.
        :return: URL as a string.
        """
        return reverse('view_campaign_detail', args=[str(self.id)])

    # ... otros métodos ...

    # Método para actualizar el conteo de likes, si es necesario.
    def update_likes_count(self):
        self.likes_count = self.likers.count()
        self.save(update_fields=['likes_count'])


class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='resources_files/', blank=True, null=True, max_length=1000)  # Considerando archivos de hasta 1G
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Community', blank=True)  # Suponiendo que ya tienes un modelo Community
    saved_contents = GenericRelation(SavedContent)
    likes_count = models.PositiveIntegerField(default=0)

    def get_absolute_url(self):
        return reverse('view_resource_detail', args=[str(self.id)])

    


class CampaignLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey(CrowdfundingCampaign, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'campaign')  

class CampaignComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey(CrowdfundingCampaign, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comentario de {self.user.username} en la campaña ID: {self.campaign.id}"




class ResourceComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Comentario de {self.user.username} en el recurso ID: {self.resource.id}"
    

class ResourceLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_likes_count()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_likes_count()

    def update_likes_count(self):
        self.resource.likes_count = self.resource.resourcelike_set.count()
        self.resource.save()

