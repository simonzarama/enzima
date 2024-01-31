from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    personal_link = models.URLField(max_length=200, blank=True) 

    def __str__(self):
        return self.user.username

# Crear un UserProfile automáticamente cuando se crea un nuevo User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Guardar el UserProfile automáticamente cuando se guarda un User
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


class Community(models.Model):
    # Campos existentes
    name = models.CharField(max_length=100, unique=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    followers = models.ManyToManyField(
        'auth.User',
        related_name='followed_communities',
        blank=True  # Permite comunidades sin seguidores
    )

    # Relación con ChatGroup como una referencia de cadena
    chat_group = models.OneToOneField(
        'ChatGroup',  # Usando el nombre del modelo como una cadena
        on_delete=models.CASCADE,
        related_name='community',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    @property
    def follower_count(self):
        return self.followers.count()

    class Meta:
        ordering = ['-created_at']

        
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



from ckeditor.fields import RichTextField
#RETOMANDO DESPUÉS DEL BREAK



class Trial(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = RichTextField(blank=True)
    media_file = models.FileField(upload_to='trials/', blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    participation_criteria = RichTextField(blank=True, null=True)
  # Nuevo campo para los criterios de participación
    interaction_count = models.PositiveIntegerField(default=0) 

    administrators = models.ManyToManyField(User, related_name='administered_trials', blank=True)
    medical_supervisor = models.ForeignKey(User, related_name='supervised_trials', on_delete=models.SET_NULL, null=True, blank=True)
    communities = models.ManyToManyField(Community, blank=True)

    include_crowdfunding = models.BooleanField(default=False)
    goal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_donors = models.PositiveIntegerField(default=0)

    saved_contents = GenericRelation(SavedContent)  # Contenidos guardados asociados

    def clean(self):
        # Validación que no depende de relaciones many-to-many
        if self.include_crowdfunding and self.goal is None:
            raise ValidationError("Debe establecer una meta de recaudación para el crowdfunding.")

    def save(self, *args, **kwargs):
        if not self.pk:  # Si es un nuevo objeto
            self.clean()
        super(Trial, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Devuelve la URL absoluta para una instancia de Trial.
        :return: URL as a string.
        """
        return reverse('view_trial_detail', args=[str(self.id)])
    
    def update_donation(self, amount):
        print("Before update:", self.total_raised, self.total_donors)
        self.total_raised += amount
        self.total_donors += 1
        self.save()
        print("After update:", self.total_raised, self.total_donors)
    

class MessageNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación de mensaje para {self.user.username}: {self.message}"

class TrialComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)




class Application(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='applications')
    wants_to_apply = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meets_requirements = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application by {self.user.username} for {self.trial.title}"



class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='notifications')




class ChatGroup(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='chat_groups')

    @staticmethod
    def get_or_create_chat(user1, user2):
        # Esta consulta busca grupos de chat que contienen exactamente a ambos usuarios y solo a ellos.
        chat = ChatGroup.objects.annotate(
            num_members=models.Count('members')
        ).filter(
            num_members=2, members=user1
        ).filter(
            members=user2
        )

        if chat.exists():
            return chat.first()
        else:
            new_chat = ChatGroup.objects.create(name=f"{user2.username}")
            new_chat.members.add(user1, user2)
            return new_chat
        
    def is_two_person_chat(self):
        # Devuelve True si el chat tiene exactamente dos miembros
        return self.members.count() == 2

    def __str__(self):
        return self.name
    

    

class Message(models.Model):
    chat_group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']




class MessageReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'message']




