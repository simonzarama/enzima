from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from .forms import CreateCommunityForm
from django.shortcuts import get_object_or_404
from .forms import CreatePostForm
from .models import User
from .models import Post, Community, Like
from django.http import JsonResponse
from .models import SavedContent
from .models import Comment
from django.db.models import Q
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from .forms import CrowdfundingCampaignForm
from django.shortcuts import get_object_or_404, reverse
from django.contrib.auth.models import User
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import CrowdfundingCampaign, CampaignLike
from .forms import CrowdfundingCampaignForm  
from .forms import ResourceForm
from .models import Resource
from .models import ResourceComment
from django.contrib.contenttypes.models import ContentType
from .models import ResourceLike
from .models import CampaignComment
from django.db.models import Count
from dal import autocomplete
from .models import Notification




# ... Resto del código de la vista ...





MODEL_MAP = {
    "campaign": "CrowdfundingCampaign",
    'post': 'Post',
    'resource': 'Resource',
    # "otro_slug": "OtroModelName",
}








def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)  # Opcional: Iniciar sesión automáticamente después del registro
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})



def landing(request):
    return render(request, 'landing.html')



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Autenticar al usuario
            user = authenticate(request, username=username, password=password)
            
            # Si las credenciales son correctas y el usuario es válido, iniciar sesión
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                # En caso contrario, puedes agregar un mensaje de error
                form.add_error(None, "Usuario o contraseña incorrecta")

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})



from django.contrib.contenttypes.models import ContentType



def home(request):
    resources = Resource.objects.all()
    campaigns = CrowdfundingCampaign.objects.all()
    top_communities = Community.objects.annotate(
        num_followers=Count('followers')
    ).order_by('-num_followers', '-created_at')[:9]

    # La lógica para obtener los recursos y campañas likeados/guardados por el usuario sigue aquí
    if request.user.is_authenticated:
        liked_resource_ids = set(ResourceLike.objects.filter(user=request.user).values_list('resource_id', flat=True))
        content_type_resource = ContentType.objects.get_for_model(Resource)
        saved_resource_ids = set(SavedContent.objects.filter(user=request.user, content_type=content_type_resource).values_list('object_id', flat=True))

        for resource in resources:
            resource.is_liked = resource.id in liked_resource_ids
            resource.is_saved = resource.id in saved_resource_ids

        # Similarmente, puedes agregar cualquier lógica adicional para las campañas como hiciste con los recursos
        # ...

    # Asegúrate de agregar 'top_communities' al contexto
    return render(request, 'home.html', {
        'resources': resources,
        'campaigns': campaigns,
        'top_communities': top_communities,
    })

def get_campaigns(request):
    campaigns = CrowdfundingCampaign.objects.all().values('title', 'description')  # Puedes agregar más campos si lo deseas
    return JsonResponse(list(campaigns), safe=False)



@login_required
def cart(request):
    return render(request, 'cart.html')









def explore(request):
    # Cuando tengas las comunidades con las propiedades 'followers' y 'created_at' puedes descomentar estas líneas
    # top_communities = Community.objects.annotate(
    #     num_followers=Count('followers')
    # ).order_by('-num_followers', '-created_at')[:10]

    # Por ahora, usa esta versión que selecciona simplemente las primeras 10 comunidades de la base de datos
    top_communities = Community.objects.all()[:10]

    context = {
        'top_communities': top_communities,
    }
    return render(request, 'explore.html', context)



def create_community_view(request):
    if request.method == 'POST':
        form = CreateCommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)  # Guarda la comunidad sin enviarla a la base de datos todavía

            # Crear y guardar un ChatGroup asociado
            chat_group_name = f"{community.name} Group Chat"
            chat_group = ChatGroup.objects.create(name=chat_group_name)
            community.chat_group = chat_group

            community.save()  # Ahora guarda la comunidad con su grupo de chat

            return redirect('view_community', community_name=community.name)
    else:
        form = CreateCommunityForm()

    context = {'form': form}
    return render(request, 'create_community.html', context)




def view_community(request, community_name):
    community = get_object_or_404(Community, name=community_name)
    
    # Obtén el criterio de ordenamiento de la URL, si no hay ninguno, ordena por published_at descendente
    order = request.GET.get('order', '-published_at')
    
    posts = Post.objects.filter(community=community).order_by(order)
    campaigns = CrowdfundingCampaign.objects.filter(communities=community).order_by(order)
    
    # Agregar el estado de "like" a cada post
    for post in posts:
        post.is_liked = request.user.is_authenticated and post.is_liked_by(request.user)

    for campaign in campaigns:
        campaign.is_liked = request.user.is_authenticated and campaign.is_liked_by(request.user)
        campaign.likes_count = campaign.likers.count()
        # Asumiendo que tienes un método para obtener el recuento de likes en el modelo Campaign
        campaign.likes_count = campaign.likers.count()
    
    # Obtener el recuento de posts
    post_count = posts.count()
    
    return render(request, 'view_community.html', {
        'posts': posts, 
        'campaigns': campaigns,  # Asegúrate de incluir las campañas en el contexto
        'community': community, 
        'post_count': post_count,
  })


@login_required
def create_post_view(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if request.method == 'POST':
        form = CreatePostForm(request.POST, request.FILES)  # Añade request.FILES aquí
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.user = request.user  # Aseguramos que el usuario autenticado es el autor del post
            post.save()
            
            # Redireccionamos al usuario después de guardar el post
            return redirect('view_community', community_name=community.name)

        # En caso de que el formulario no sea válido, podrías manejar los errores aquí o simplemente 
        # permitir que la plantilla los muestre.
    else:
        form = CreatePostForm()

    # Pasamos el formulario y la comunidad a la plantilla para su renderización
    return render(request, 'create_post.html', {'form': form, 'community': community})


@login_required
def liked_content(request, username):
    user = get_object_or_404(User, username=username)
    liked_posts = Post.objects.filter(like__user=user)

    context = {
        'liked_posts': liked_posts,
        'profile_user': user,
    }

    return render(request, 'liked_content.html', context)

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like = Like.objects.filter(user=request.user, post=post)

    if like.exists():
        like.first().delete()
        is_liked = False
    else:
        Like.objects.create(user=request.user, post=post)
        is_liked = True

    post.refresh_from_db()  # Refresca el objeto post desde la base de datos
    likes_count = post.likes_count  # Ahora debería obtener el conteo actualizado de likes
    return JsonResponse({'is_liked': is_liked, 'post_id': post_id, 'likes_count': likes_count})



from django.http import JsonResponse

@login_required
def like_campaign(request, campaign_id):
    if request.method == 'POST':
        campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
        user_liked = campaign.likers.filter(id=request.user.id).exists()

        if user_liked:
            campaign.likers.remove(request.user)
            is_liked = False
        else:
            campaign.likers.add(request.user)
            is_liked = True

        campaign.update_likes_count()  # Usamos el método del modelo

    return JsonResponse({
        'success': True,
        'is_liked': is_liked,
        'campaign_id': campaign_id,
        'likes_count': campaign.likes_count
    })

@login_required
def like_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    like = ResourceLike.objects.filter(user=request.user, resource=resource)

    if like.exists():
        like.first().delete()
        is_liked = False
    else:
        ResourceLike.objects.create(user=request.user, resource=resource)
        is_liked = True

    resource.refresh_from_db()
    likes_count = resource.likes_count
    return JsonResponse({'is_liked': is_liked, 'resource_id': resource_id, 'likes_count': likes_count})




@login_required
def save_content(request, content_type_model, content_id):
    # Mapear el slug al nombre real del modelo
    model_name = MODEL_MAP.get(content_type_model, None)
    if not model_name:
        if content_type_model == 'trial':
            model_name = 'Trial'
        else:
            return JsonResponse({"error": "Modelo no válido"}, status=400)

    # Obtener el modelo del contenido
    model = apps.get_model(app_label='myapp', model_name=model_name)
    content = get_object_or_404(model, id=content_id)

    # Determina el ContentType del modelo
    content_type = ContentType.objects.get_for_model(model)

    # Verificar si el usuario ya ha guardado este contenido
    already_saved = SavedContent.objects.filter(user=request.user, content_type=content_type, object_id=content.id).exists()

    if already_saved:
        # Si ya está guardado, eliminarlo
        print(f"Eliminando {model_name} con ID {content_id} de los contenidos guardados de {request.user.username}.")
        SavedContent.objects.filter(user=request.user, content_type=content_type, object_id=content.id).delete()
        saved = False
    else:
        print(f"Guardando {model_name} con ID {content_id} para {request.user.username}.")
        # Si no está guardado, crear un nuevo registro en SavedContent
        SavedContent.objects.create(user=request.user, content_type=content_type, object_id=content.id)
        saved = True
        
        if isinstance(content, Trial):
            content.interaction_count += 1
            content.save()


    return JsonResponse({"saved": saved})

def saved_content(request, username):
    user = get_object_or_404(User, username=username)
    
    # Esto ya estaba aquí: obtener todos los elementos guardados por el usuario
    saved_items = SavedContent.objects.filter(user=user)

    # Obtener el tipo de contenido para CrowdfundingCampaign
    campaign_content_type = ContentType.objects.get_for_model(CrowdfundingCampaign)
    
    # Obtener todas las campañas guardadas por el usuario
    saved_campaigns = SavedContent.objects.filter(user=user, content_type=campaign_content_type)

    # Obtener el tipo de contenido para Resource
    resource_content_type = ContentType.objects.get_for_model(Resource)

    # Obtener todos los recursos guardados por el usuario
    saved_resources = SavedContent.objects.filter(user=user, content_type=resource_content_type)

    
        # Obtener el tipo de contenido para Trial
    trial_content_type = ContentType.objects.get_for_model(Trial)

    # Obtener todos los ensayos guardados por el usuario
    saved_trials = SavedContent.objects.filter(user=user, content_type=trial_content_type)

    # Actualizar el contexto
    context = {
        'saved_items': saved_items,
        'saved_campaigns': saved_campaigns,
        'saved_resources': saved_resources,
        'saved_trials': saved_trials,  # Esto son los ensayos guardados
        'profile_user': user,
    }


    return render(request, 'profile-saved.html', context)


class EditPostView(View):
    template_name = 'edit_post.html'

    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        return render(request, self.template_name, {'post': post})
    

class DeletePostView(View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        community_url = reverse('view_community', args=[post.community.name])
        post.delete()
        return JsonResponse({'redirect_url': community_url})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_liked = request.user.is_authenticated and post.is_liked_by(request.user)  # Verifica si el usuario ha dado 'like' al post
    context = {
        'post': post,
        'is_liked': is_liked,  # Agrega 'is_liked' al contexto
    }
    return render(request, 'post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    response_data = {}
    if request.method == 'POST':
        text = request.POST.get('comment_text')
        new_comment = Comment.objects.create(user=request.user, post=post, text=text)
        response_data['username'] = request.user.username
        response_data['text'] = new_comment.text
        response_data['comment_id'] = new_comment.id
        response_data['is_owner'] = True  # Dado que el usuario acaba de crear este comentario, es el propietario
    return JsonResponse(response_data)




def search_results(request):
    query = request.GET.get('q', '')
    
    # Aquí deberás buscar en tus modelos según el término de búsqueda. 
    # Supondré que tienes modelos llamados Community, Post y User.
    communities = Community.objects.filter(name__icontains=query)
    posts = Post.objects.filter(title__icontains=query)
    users = User.objects.filter(username__icontains=query)

    context = {
        'query': query,
        'communities': communities,
        'posts': posts,
        'users': users,
    }
    return render(request, 'search_results.html', context)





def community_results(request):
    # Imaginemos que obtienes tus comunidades de una base de datos
    communities = Community.objects.filter(name__icontains=request.GET['q'])
    return render(request, 'community_results.html', {'communities': communities})

def user_results(request):
    # Imaginemos que obtienes tus usuarios de una base de datos
    users = User.objects.filter(username__icontains=request.GET['q'])
    return render(request, 'user_results.html', {'users': users})

def post_results(request):
    # Imaginemos que obtienes tus publicaciones de una base de datos
    posts = Post.objects.filter(title__icontains=request.GET['q'])
    return render(request, 'post_results.html', {'posts': posts})







def ctg_obtener_ensayos(query):
    print(f"Buscando: {query}")

    # Inicializa una sesión con reintentos
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    ctg_base_url = "https://classic.clinicaltrials.gov/api/query/study_fields"
 # esta ha funcionado a veces: "https://ClinicalTrials.gov/api/query/study_fields"
    params = {
        'expr': query,
        'fields': 'NCTId,BriefTitle,OverallStatus,LocationCity,Condition,Rank',  # Asegúrate de pedir estos campos
        'fmt': 'json'
    }

    try:
        response = session.get(ctg_base_url, params=params, timeout=10)  # 10 segundos de tiempo de espera
        response.raise_for_status()  # Esto lanzará un error si el código HTTP es 4xx o 5xx

        # Asegúrate de ajustar la clave de acceso en el JSON si es necesario.
        return response.json()['StudyFieldsResponse']['StudyFields']
    except requests.RequestException as e:
        print(f"Error al obtener datos de ClinicalTrials.gov: {e}")
        return []

    

    

def ctg_ensayos_view(request):
    query = request.GET.get('query', '')
    print(f"Query desde la vista: {query}")
    ctg_ensayos = ctg_obtener_ensayos(query) if query else []
    return render(request, 'ctg_listado.html', {'ensayos': ctg_ensayos, 'query': query})



@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.user:  # verifica que el usuario sea el propietario del post
        post.delete()
        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'forbidden'}, status=403)
    



@method_decorator(login_required, name='dispatch')
class EditPostView(View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        # Verifica que el usuario que hace la solicitud es el propietario del post
        if request.user != post.user:
            return JsonResponse({'error': 'No tienes permiso para editar este post.'}, status=403)

        title = request.POST.get('title')
        content = request.POST.get('content')
        media_file = request.FILES.get('media_file')
        remove_media_file = request.POST.get('remove_media_file') == 'true'  # Convertir la cadena 'true' a un booleano

        if title:
            post.title = title
        if content:
            post.content = content
        if media_file:
            post.media_file = media_file
        elif remove_media_file:
            post.media_file.delete()  # Esto eliminará el archivo del sistema de archivos y pondrá el campo `media_file` en None.

        post.save()

        return JsonResponse({
        'success': True,
        'message': 'Post actualizado exitosamente.',
        'title': post.title,
        'content': post.content,
        'media_url': post.media_file.url if post.media_file else ''
    })

def post_content(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'post_content.html', {'post': post})


def get_post_data(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    data = {
        'title': post.title,
        'content': post.content,
    }
    return JsonResponse(data)

def create_crowdfunding_campaign(request):
    if request.method == 'POST':
        form = CrowdfundingCampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)  # No guardes aún
            campaign.creator = request.user  # Establece el usuario actual como creador
            campaign.save()  # Guarda la campaña

            form.save_m2m()  # Guarda las relaciones many-to-many, en este caso 'communities'

            return redirect(campaign.get_absolute_url())
    else:
        form = CrowdfundingCampaignForm()

    return render(request, 'create_campaign.html', {'form': form})


def view_campaign_detail(request, campaign_id):
    campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
    donation_progress = campaign.total_donations / campaign.goal * 100
    
    # Obtener comunidades asociadas a la campaña
    associated_communities = campaign.communities.all()

    liked_campaign_ids = set(CampaignLike.objects.filter(user=request.user).values_list('campaign_id', flat=True))

        # Actualiza el estado de 'like' para cada campaña
    
    campaign.is_liked = request.user.is_authenticated and campaign.is_liked_by(request.user)
    print(f"Campaign ID: {campaign.id}, Is Liked: {campaign.is_liked}") 

    # Verificar si el contenido está guardado para el usuario actual
    is_saved = False
    if request.user.is_authenticated:
        is_saved = campaign.saved_contents.filter(user=request.user).exists()

    # Pasa donation_progress, associated_communities y is_saved al contexto
    context = {
    'campaign': campaign,
    'donation_progress': donation_progress,
    'associated_communities': associated_communities,
    'is_saved': is_saved
    }

    return render(request, 'crowdfunding_detail.html', context)



@login_required #esto es para poner la campaña en guardados
def save_campaign(request, campaign_id):
    campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
    
    if campaign in request.user.savedcontent.saved_campaigns.all():
        request.user.savedcontent.saved_campaigns.remove(campaign)
        saved = False
    else:
        request.user.savedcontent.saved_campaigns.add(campaign)
        saved = True
    
    return JsonResponse({'saved': saved})


def get_campaign_data(request, campaign_id):
    campaign = get_object_or_404(CrowdfundingCampaign, pk=campaign_id)
    data = {
        'title': campaign.title,
        'description': campaign.description,
        # ... otros campos que necesites ...
    }
    return JsonResponse(data)


@login_required
@require_POST
def update_campaign(request, campaign_id):
    campaign = get_object_or_404(CrowdfundingCampaign, pk=campaign_id)
    
    # Solo permitir que el creador de la campaña la actualice
    if request.user != campaign.creator:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Crear una instancia del formulario con los datos enviados y el archivo (si existe)
    form = CrowdfundingCampaignForm(request.POST, request.FILES, instance=campaign)
    
    # Comprobar si el formulario es válido
    if form.is_valid():
        # Verificar si se pidió eliminar el archivo actual
        if 'remove_media_file' in request.POST and request.POST['remove_media_file'] == 'true':
            if campaign.media_file:
                campaign.media_file.delete()  # Elimina el archivo del sistema de archivos.
                campaign.media_file = None    # Elimina la referencia al archivo del objeto de campaña.

        # Guardar los cambios del formulario y los campos del modelo
        form.save()

        # Recargar la instancia del modelo para reflejar los cambios en la base de datos
        campaign.refresh_from_db()

        # Preparar la respuesta JSON con los datos actualizados
        return JsonResponse({
            'success': True,
            'title': campaign.title,
            'description': campaign.description,
            'current_media_filename': campaign.media_file.name.split('/')[-1] if campaign.media_file else None,
            'media_url': campaign.media_file.url if campaign.media_file else None,
            # ... otros campos ...
        })
    else:
        # Si el formulario no es válido, enviar los errores en la respuesta JSON
        return JsonResponse({'error': form.errors}, status=400)

def donate_view(request):
    return render(request, 'donate_view')

class EditCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para editar este comentario.'}, status=403)
        text = request.POST.get('text')
        if text:
            comment.text = text
            comment.save()
        return JsonResponse({'success': True, 'text': comment.text})

class DeleteCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para eliminar este comentario.'}, status=403)
        comment.delete()
        return JsonResponse({'success': True})
    

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Obtiene el ContentType para el modelo Post
    post_content_type = ContentType.objects.get_for_model(Post)
    
    # Obtiene todos los SavedContent que contienen Posts para el usuario
    saved_contents = SavedContent.objects.filter(user=user, content_type=post_content_type)
    
    # Obtiene los objetos Post de todos los SavedContent
    saved_posts = [content.content_object for content in saved_contents]

    context = {
        'profile_user': user,
        'saved_posts': saved_posts,
        # ... otros contextos que estés usando ...
    }

    return render(request, 'profile.html', context)


import logging

# Configura el logging
logger = logging.getLogger(__name__)

def delete_campaign(request, campaign_id):
    # Depuración: inicio de la solicitud de eliminación
    logger.debug(f"Delete campaign request for id {campaign_id} received.")
    
    if request.method == "POST":
        logger.debug("Request method is POST.")
        
        try:
            campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
            if request.user.is_authenticated and campaign.creator == request.user:
                logger.debug(f"User {request.user.username} is authenticated and authorized to delete campaign {campaign_id}.")
                campaign.delete()
                logger.debug(f"Campaign {campaign_id} deleted successfully.")
                return JsonResponse({'status': 'success', 'message': 'Campaign deleted successfully'})
            else:
                logger.warning(f"Unauthorized attempt to delete campaign {campaign_id} by user {request.user.username}.")
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        except CrowdfundingCampaign.DoesNotExist:
            logger.error(f"Campaign with id {campaign_id} does not exist.")
            return JsonResponse({'status': 'error', 'message': 'Campaign does not exist'}, status=404)
    else:
        logger.warning("Invalid request method.")
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    
def community_posts(request, community_name):
    community = get_object_or_404(Community, name=community_name)
    
    # Obtén el criterio de ordenamiento de la URL, si no hay ninguno, ordena por published_at descendente
    order = request.GET.get('order', '-published_at')
    
    posts = Post.objects.filter(community=community).order_by(order)
    
    # Agregar el estado de "like" a cada post
    if request.user.is_authenticated:
    # Agregar el estado de "like" a cada post
        for post in posts:
            post.is_liked = post.is_liked_by(request.user)

        # Obtener los IDs de los posts guardados por el usuario
        content_type_post = ContentType.objects.get_for_model(Post)
        saved_post_ids = SavedContent.objects.filter(user=request.user, content_type=content_type_post).values_list('object_id', flat=True)
    else:
        for post in posts:
            post.is_liked = False
        saved_post_ids = []
    post_count = posts.count()

    return render(request, 'community_posts.html', {
        'community': community,
        'posts': posts,
        'post_count': post_count,
        'saved_post_ids': saved_post_ids  # añadir este contexto para usarlo en el template
    })


from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType



def community_resources(request, community_name):
    community = get_object_or_404(Community, name=community_name)
    resources = Resource.objects.filter(tags=community)

    # Obtener el tipo de contenido para Resource
    content_type_resource = ContentType.objects.get_for_model(Resource)

    # Obtener los IDs de los recursos guardados por el usuario
    saved_resource_ids = SavedContent.objects.filter(
        user=request.user, 
        content_type=content_type_resource
    ).values_list('object_id', flat=True)

    # Añadir atributos 'is_liked' y 'is_saved' a cada recurso
    for resource in resources:
        resource.is_liked = ResourceLike.objects.filter(user=request.user, resource=resource).exists()
        resource.is_saved = resource.id in saved_resource_ids

    return render(request, 'community_resources.html', {
        'community': community,
        'resources': resources,
        'saved_resource_ids': saved_resource_ids  # Pasar esto al contexto para la plantilla
    })


from django.contrib.contenttypes.models import ContentType


def all_resources(request):
    resources = Resource.objects.all()
    content_type_resource = ContentType.objects.get_for_model(Resource)
    
    saved_resource_ids = SavedContent.objects.filter(
        user=request.user, 
        content_type=content_type_resource
    ).values_list('object_id', flat=True)

    for resource in resources:
        resource.is_liked = ResourceLike.objects.filter(user=request.user, resource=resource).exists()
        resource.is_saved = resource.id in saved_resource_ids

    return render(request, 'resources.html', {
        'resources': resources,
        'saved_resource_ids': saved_resource_ids
    })


# Obtener los IDs de los Trials guardados por el usuario actualAAAAAAAAAAAAAAAAAAAAAAAAAA


def all_trials(request):
    # Obtener el parámetro 'order' de la URL, con un valor predeterminado
    order = request.GET.get('order', '-published_at')
    print("Orden recibido en la vista all_trials:", order)

    # Asegúrate de que el valor de 'order' sea uno de los esperados
    if order not in ['-published_at', '-interaction_count']:
        order = '-published_at'

    # Ordenar los trials basándose en el parámetro 'order'
    trials = Trial.objects.order_by(order)

    content_type_trial = ContentType.objects.get_for_model(Trial)

    # Obtener los IDs de los Trials guardados por el usuario actual
    if request.user.is_authenticated:
        saved_trial_ids = SavedContent.objects.filter(
            user=request.user,
            content_type=content_type_trial
        ).values_list('object_id', flat=True)

        for trial in trials:
            trial.is_saved = trial.id in saved_trial_ids
    else:
        saved_trial_ids = []  # Inicializar saved_trial_ids como una lista vacía
        for trial in trials:
            trial.is_saved = False

    return render(request, 'trials.html', {
        'trials': trials,
        'saved_trial_ids': saved_trial_ids
    })

# Obtener los IDs de los Trials guardados por el usuario actualAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA


def all_crowdfunding(request):
    campaigns = CrowdfundingCampaign.objects.all()
    content_type_campaign = ContentType.objects.get_for_model(CrowdfundingCampaign)
    
    if request.user.is_authenticated:
        saved_campaign_ids = SavedContent.objects.filter(
            user=request.user, 
            content_type=content_type_campaign
        ).values_list('object_id', flat=True)

        liked_campaign_ids = set(CampaignLike.objects.filter(user=request.user).values_list('campaign_id', flat=True))

        for campaign in campaigns:
            campaign.is_liked = campaign.is_liked_by(request.user)
            campaign.is_saved = campaign.id in saved_campaign_ids
    else:
        for campaign in campaigns:
            campaign.is_liked = False
            campaign.is_saved = False
    
    for campaign in campaigns:
        campaign.is_saved = campaign.id in saved_campaign_ids

    print(campaigns)

    return render(request, 'crowdfunding.html', {
        'campaigns': campaigns,
        'saved_campaign_ids': saved_campaign_ids
    })


# Obtener los IDs de los Trials guardados por el usuario actualAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA






from django.contrib.contenttypes.models import ContentType



def community_trials(request, community_name):
    # Obtener la comunidad por su nombre
    community = get_object_or_404(Community, name=community_name)

    # Imprimir para depuración
    print("Community Name:", community_name)

    # Filtrar los trials asociados a la comunidad
    # Obtener el parámetro 'order' de la URL, con un valor predeterminado
    order = request.GET.get('order', '-published_at')

    # Imprimir para depuración
    print("Order from GET request:", order)

    # Asegúrate de que el valor de 'order' sea uno de los esperados
    if order not in ['-published_at', '-interaction_count']:
        order = '-published_at'

    # Filtrar los trials asociados a la comunidad y ordenarlos
    trials = Trial.objects.filter(communities=community).order_by(order).distinct()

    # Imprimir los trials filtrados para depuración
    print("Filtered Trials for Community:", list(trials.values('id', 'title')))

    # Obtener el tipo de contenido para Trial
    content_type_trial = ContentType.objects.get_for_model(Trial)

    # Obtener los IDs de los Trials guardados por el usuario
    if request.user.is_authenticated:
    # Obtener los IDs de los Trials guardados por el usuario
        saved_trial_ids = SavedContent.objects.filter(
            user=request.user, 
            content_type=content_type_trial
        ).values_list('object_id', flat=True)
    else:
        saved_trial_ids = []

    # Renderizar la plantilla con los datos necesarios
    return render(request, 'community_trials.html', {
        'community': community,
        'trials': trials,
        'saved_trial_ids': saved_trial_ids
    })

from .forms import UserProfileForm
from django.http import HttpResponseForbidden


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)

    # Comprueba si el usuario actual tiene permiso para editar este perfil
    if not request.user == user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user.userprofile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)
    else:
        form = UserProfileForm(instance=user.userprofile)

    return render(request, 'edit_profile.html', {'form': form})



def add_resource(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)  # No guardes aún
            resource.creator = request.user  # Establece el usuario actual como creador
            resource.save()  # Guarda el recurso

            form.save_m2m()  # Guarda las relaciones many-to-many, en este caso 'tags'

            return redirect(resource.get_absolute_url())
    else:
        form = ResourceForm()

    return render(request, 'add_resource.html', {'form': form})


# En tu archivo views.py
from django.contrib.contenttypes.models import ContentType

def view_resource_detail(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)

    # Determinar si el recurso ha sido guardado por el usuario actual
    is_saved = False  # Valor predeterminado
    if request.user.is_authenticated:  # Asegúrate de que el usuario esté autenticado
        is_saved = SavedContent.objects.filter(
            user=request.user, 
            content_type=ContentType.objects.get_for_model(Resource), 
            object_id=resource.id
        ).exists()

    is_liked = resource.resourcelike_set.filter(user=request.user).exists()
    context = {
        'resource': resource,
        'is_saved': is_saved,
        'is_liked': is_liked,
    }

    return render(request, 'resource_detail.html', context)





# Vista para agregar un comentario a un recurso
@login_required
def add_comment_to_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    response_data = {}
    if request.method == 'POST':
        text = request.POST.get('comment_text')
        new_comment = ResourceComment.objects.create(user=request.user, resource=resource, text=text)
        response_data['username'] = request.user.username
        response_data['text'] = new_comment.text
        response_data['comment_id'] = new_comment.id
        response_data['is_owner'] = True  # El usuario es el propietario del comentario
        response_data['comment_count'] = resource.comments.count()

    return JsonResponse(response_data)

class EditResourceCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(ResourceComment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para editar este comentario.'}, status=403)
        text = request.POST.get('text')
        if text:
            comment.text = text
            comment.save()
        return JsonResponse({'success': True, 'text': comment.text})

class DeleteResourceCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(ResourceComment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para eliminar este comentario.'}, status=403)
        comment.delete()
        return JsonResponse({'success': True})



from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import CrowdfundingCampaign

@login_required
@require_POST
def update_campaign_ajax(request, campaign_id):
    try:
        # Intenta obtener la campaña; si no existe, se captura la excepción.
        campaign = CrowdfundingCampaign.objects.get(pk=campaign_id)
        
        # Asegurarse de que el usuario que hace la solicitud es el creador de la campaña.
        if request.user != campaign.creator:
            return JsonResponse({"success": False, "message": "No autorizado."}, status=403)

        # Procede a actualizar la campaña.
        campaign.title = request.POST.get('title')
        campaign.description = request.POST.get('description')
        # ... otros campos ...
        campaign.save()

        # Retorna una respuesta positiva al actualizar con éxito.
        return JsonResponse({"success": True, "message": "Campaña actualizada correctamente."})

    except CrowdfundingCampaign.DoesNotExist:
        # Retorna una respuesta de error si la campaña no existe.
        return JsonResponse({"success": False, "message": "Campaña no encontrada."}, status=404)

    except Exception as e:
        # Manejo genérico de excepciones, podría capturar otros errores no previstos.
        return JsonResponse({"success": False, "message": "Error al actualizar la campaña: {}".format(str(e))}, status=500)



class AddCampaignCommentView(View):
    def post(self, request, campaign_id):
        campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
        text = request.POST.get('comment_text')
        if text:
            comment = CampaignComment.objects.create(user=request.user, campaign=campaign, text=text)
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'created': comment.created.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
        return JsonResponse({'success': False, 'error': 'Comment text is required.'})

class EditCampaignCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(CampaignComment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para editar este comentario.'}, status=403)
        text = request.POST.get('text')
        if text:
            comment.text = text
            comment.save()
        return JsonResponse({'success': True, 'text': comment.text})

class DeleteCampaignCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(CampaignComment, id=comment_id)
        if request.user != comment.user:
            return JsonResponse({'error': 'No tienes permiso para eliminar este comentario.'}, status=403)
        comment.delete()
        return JsonResponse({'success': True})





class EditResourceView(View):
    template_name = 'edit_resource.html'  # Cambia esto por la plantilla adecuada si es diferente

    def get(self, request, resource_id):
        resource = get_object_or_404(Resource, pk=resource_id)
        return render(request, self.template_name, {'resource': resource})
    

    


@login_required
@require_POST
def update_resource_ajax(request, resource_id):
    print(f"Inicio de update_resource_ajax para el resource ID {resource_id} por el usuario {request.user.username}")
    
    resource = get_object_or_404(Resource, pk=resource_id)
    print(f"Resource con ID {resource_id} obtenido exitosamente")

    # Solo permitir que el creador del recurso lo actualice
    if request.user != resource.creator:
        print(f"Usuario {request.user.username} no autorizado para actualizar el resource ID {resource_id}")
        return JsonResponse({'error': 'Not authorized'}, status=403)

    form = ResourceForm(request.POST, request.FILES, instance=resource)
    if form.is_valid():
        form.save()
        print(f"Resource con ID {resource_id} actualizado exitosamente por el usuario {request.user.username}")
        selected_tags_ids = request.POST.getlist('tags')  # Esto obtiene una lista de los IDs seleccionados
        selected_tags = Community.objects.filter(id__in=selected_tags_ids)
        resource.tags.set(selected_tags)
        resource.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'title': resource.title,
            'description': resource.description,
            'current_media_filename': resource.file.name.split('/')[-1] if resource.file else None,
            'media_url': resource.file.url if resource.file else None,
            # ... otros campos si los hay ...
        })
    else:
        print(f"Errores durante la actualización del resource ID {resource_id}: {form.errors}")
        return JsonResponse({'error': form.errors}, status=400)


@login_required
@require_POST
def delete_resource(request, resource_id):
    resource = get_object_or_404 (Resource, id=resource_id)
    if request.user == resource.creator:
        resource.delete()
        return JsonResponse({'status': 'success', 'message': 'Resource deleted successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
from django.http import JsonResponse
from .models import Resource  # Asumo que tienes un modelo llamado Resource

def get_resource_data(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)

    data = {
        'title': resource.title,
        'description': resource.description,
        # Añade cualquier otro campo que necesites enviar al frontend
        # Por ejemplo, si tu modelo Resource tiene un campo para la URL del medio:
        'media_url': resource.file.url if resource.file else None,

    }

    return JsonResponse(data)



def edit_resource(request, resource_id):
    if request.method == 'POST':
        # Aquí va tu lógica para editar el recurso
        # Por ejemplo:
        resource = Resource.objects.get(pk=resource_id)
        # Actualiza los campos del recurso con los datos del POST...
        resource.title = request.POST.get('title')
        resource.description = request.POST.get('description')
        # ...otros campos...
        resource.save()

        return JsonResponse({"status": "success", "message": "Resource updated successfully."})

    # Si no es POST, puedes devolver un error o simplemente renderizar la página de edición.
    return JsonResponse({"status": "error", "message": "Invalid request method."})










#DESPUES DEL BREAK

from django.shortcuts import render, redirect
from .forms import TrialForm  # Asegúrate de crear este formulario con los campos necesarios
from .models import Trial  # Importa el modelo Trial
from .models import TrialComment 




def create_trial(request):
    if request.method == 'POST':
        form = TrialForm(request.POST, request.FILES)
        if form.is_valid():
            trial = form.save(commit=False)

            # Guardar primero el objeto Trial para que tenga un ID
            trial.save()

            administrators = form.cleaned_data.get('administrators')
            
            # Asegurarse de que el usuario actual esté incluido en los administradores
            if request.user not in administrators.all():
                administrators = list(administrators) + [request.user]
            
            # Validación de la cantidad de administradores
            if len(administrators) > 3:
                messages.error(request, "No se pueden asignar más de 3 administradores.")
                return render(request, 'create_trial.html', {'form': form})

            trial.administrators.set(administrators)

            # Aquí puedes manejar la lógica de compromiso para crowdfunding
            if form.cleaned_data.get('include_crowdfunding'):
                # Implementa la lógica necesaria aquí
                pass

            form.save_m2m()  # Guarda las relaciones many-to-many

            # Redirigir a una página de éxito o similar
            return redirect('home')  # Asegúrate de tener esta URL configurada en urls.py

    else:
        form = TrialForm()

    return render(request, 'create_trial.html', {'form': form})





class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(username__icontains=self.q)

        return qs
    

class CommunityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Aquí asumo que tu modelo Community tiene un campo 'name' para filtrar
        # Modifica esta lógica según tu modelo real
        if not self.request.user.is_authenticated:
            return Community.objects.none()

        qs = Community.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs




from .models import Trial, Application
from .forms import ApplicationForm  # Asegúrate de haber creado este formulario

def trial_detail(request, id):
    trial = get_object_or_404(Trial, pk=id)

    if request.user.is_authenticated:
        is_administrator = request.user in trial.administrators.all()
        already_applied = Application.objects.filter(trial=trial, user=request.user, wants_to_apply=True).exists()
    else:
        is_administrator = False
        already_applied = False

    form = ApplicationForm()

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = ApplicationForm(request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.trial = trial
                application.user = request.user
                if not application.wants_to_apply:
                    application.meets_requirements = False
                application.save()

                # Notificar a los administradores de cualquier nueva aplicación
                for admin in trial.administrators.all():
                    Notification.objects.create(
                        user=admin,
                        message=f"New message for {trial.title} by {request.user.username}.",
                        trial=trial
                    )

                return redirect('view_trial_detail', id=id)
        else:
            # Manejar el caso de usuarios no autenticados que intenten enviar una solicitud
            # Puedes redirigirlos a la página de inicio de sesión o mostrar un mensaje de error
            return redirect('login')  # Reemplaza 'login' con el nombre de tu URL de inicio de sesión

    # Obtener las aplicaciones relacionadas con este ensayo, ordenadas por fecha de creación
    applications = Application.objects.filter(trial=trial).order_by('-created_at')

    context = {
        'trial': trial,
        'is_administrator': is_administrator,
        'form': form,
        'already_applied': already_applied,
        'applications': applications
    }

    return render(request, 'trial_detail.html', context)
class AddTrialCommentView(View):
    def post(self, request, trial_id):
        trial = get_object_or_404(Trial, id=trial_id)
        text = request.POST.get('comment_text')
        if text:
            comment = TrialComment.objects.create(user=request.user, trial=trial, text=text)
            trial.interaction_count += 1  # Añadir interacción
            trial.save()  
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'created': comment.created.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
        return JsonResponse({'success': False, 'error': 'Comment text is required.'})



class EditTrialCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(TrialComment, id=comment_id, user=request.user)
        text = request.POST.get('comment_text')
        if text:
            comment.text = text
            comment.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Comment text is required.'})

class DeleteTrialCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(TrialComment, id=comment_id, user=request.user)
        comment.delete()
        return JsonResponse({'success': True})





def edit_trial(request, id):
    trial = get_object_or_404(Trial, pk=id)

    if request.method == 'POST':
        form = TrialForm(request.POST, request.FILES, instance=trial)
        if form.is_valid():
            form.save()
            return redirect('view_trial_detail', id=id)
    else:
        form = TrialForm(instance=trial)

    return render(request, 'edit_trial.html', {'form': form, 'trial': trial})

from coinbase.wallet.client import Client
import os
from paypal.standard.forms import PayPalPaymentsForm
from .forms import DonationForm

def donate_view(request, trial_id):
    trial = get_object_or_404(Trial, pk=trial_id)
    donation_form = DonationForm(request.POST or None)

    if request.method == 'POST' and donation_form.is_valid():
        # Obtén la cantidad y el email del donante del formulario
        amount = donation_form.cleaned_data['amount']
        donor_email = donation_form.cleaned_data['donor_email']

        # Configuración de PayPal
        paypal_dict = {
            "business": os.environ.get('PAYPAL_RECEIVER_EMAIL'),
            "amount": amount,
            "item_name": f"Donación para {trial.title}",
            "invoice": str(trial.id),  # Asegúrate de que sea único
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            "return_url": request.build_absolute_uri(reverse('payment_return')),
            "cancel_return": request.build_absolute_uri(reverse('payment_cancel')),
        }

        paypal_form = PayPalPaymentsForm(initial=paypal_dict)

        # Puedes pasar tanto el formulario de PayPal como el formulario de donación a la plantilla
        return render(request, "payment/paypal_form.html", {
            "paypal_form": paypal_form,
            "donation_form": donation_form,
            "trial": trial
        })

    # Renderiza el formulario de donación en la plantilla `donate_view.html`
    return render(request, 'donate_view.html', {
        'donation_form': donation_form,
        'trial': trial
    })




@login_required
def notifications(request):
    user_notifications = request.user.notification_set.all()

    # Marcar todas las notificaciones como leídas
    user_notifications.update(is_read=True)

    return render(request, 'notifications.html', {'notifications': user_notifications})

from .models import MessageNotification

from django.utils.dateparse import parse_datetime



def check_unread_message_notifications(request):
    if request.user.is_authenticated:
        last_viewed_str = request.session.get('last_messages_viewed')
        last_viewed = parse_datetime(last_viewed_str) if last_viewed_str else None

        print(f"Última visita a los mensajes: {last_viewed}")  # Depuración

        if last_viewed:
            has_new_messages = MessageNotification.objects.filter(
                user=request.user, 
                created_at__gt=last_viewed
            ).exists()
            print(f"Has new messages: {has_new_messages}")  # Depuración
            return JsonResponse({'has_new_messages': has_new_messages})
        else:
            print("No se encontró la última visita, asumiendo mensajes nuevos.")  # Depuración
            return JsonResponse({'has_new_messages': True})
    else:
        print("Usuario no autenticado.")  # Depuración
    return JsonResponse({'has_new_messages': False})





@login_required
def trial_contact(request, trial_id):
    trial = get_object_or_404(Trial, pk=trial_id)

    if request.user not in trial.administrators.all():
        return redirect('home')

    # Obtener todas las instancias de Application para este ensayo
    applications = Application.objects.filter(trial=trial)

    context = {
        'trial': trial,
        'applications': applications,
    }

    return render(request, 'trial_contact.html', context)



@login_required
def get_application_details(request, application_id):
    application = get_object_or_404(Application, pk=application_id)

    # Comprobar si el usuario es administrador del trial asociado a la aplicación
    if request.user in application.trial.administrators.all():
        return JsonResponse({
            'success': True,
            'application': {
                'user': application.user.username,
                'meets_requirements': application.meets_requirements,
                'wants_to_apply': application.wants_to_apply,
                'message': application.message
            }
        })
    else:
        # Si el usuario no es administrador, redirigir a 'home' o mostrar un mensaje de error
        return redirect('home')  # O p
    

from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json



@csrf_exempt
def update_donation(request, trial_id):  # Ahora 'trial_id' es un parámetro de la función
    if request.method == 'POST':
        print("Received request for trial ID:", trial_id)
        data = json.loads(request.body)
        print("Received data:", data)
        amount = data.get('amount')
        
        trial = get_object_or_404(Trial, pk=trial_id)
        trial.update_donation(Decimal(amount))
        trial.interaction_count += 1  # Añadir interacción
        trial.save()  
        
        return JsonResponse({'status': 'success', 'message': 'Donation updated successfully.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



from .models import Message, MessageReadStatus
from .forms import GroupChatForm, NewChatForm
from django.db.models import Max
from django.db.models import Exists, OuterRef
from django.utils import timezone

@login_required
def messages(request, chat_group_id=None):
    request.session['last_messages_viewed'] = timezone.now().isoformat()
    if chat_group_id:
        MessageReadStatus.objects.filter(
            user=request.user, 
            message__chat_group_id=chat_group_id, 
            is_read=False
        ).update(is_read=True)

    chat_form = GroupChatForm(request.POST or None)
    new_chat_form = NewChatForm(request.POST or None)

    # Actualizar estados de mensajes no leídos para cada grupo de chat
    chat_groups = request.user.chat_groups.annotate(
        last_message_date=Max('messages__timestamp'),
        has_unread_messages=Exists(
            MessageReadStatus.objects.filter(
                message__chat_group=OuterRef('pk'),
                is_read=False,
                user=request.user
            )
        )
    ).order_by('-last_message_date')

    selected_chat_group = None
    messages = None

    if request.method == 'POST':
        if 'create_group' in request.POST and chat_form.is_valid():
            chat_group = chat_form.save(commit=False)
            chat_group.save()
            chat_group.members.add(request.user)
            chat_group.save()
            return redirect('messages')
        elif 'create_chat' in request.POST and new_chat_form.is_valid():
            chat_group = new_chat_form.save(commit=False)
            chat_group.save()
            selected_users = new_chat_form.cleaned_data['users']
            for user in selected_users:
                chat_group.members.add(user)
            chat_group.members.add(request.user)
            chat_group.save()

            # Crear MessageReadStatus para los nuevos chats
            for member in chat_group.members.exclude(id=request.user.id):
                for message in chat_group.messages.all():
                    status, created = MessageReadStatus.objects.get_or_create(
                        user=member, 
                        message=message, 
                        defaults={'is_read': False}
                    )
                    if created:
                        print(f"Creado MessageReadStatus: Usuario {member.username}, Mensaje {message.id}, No Leído")
                    else:
                        print(f"Ya existe MessageReadStatus: Usuario {member.username}, Mensaje {message.id}, Estado Leído {status.is_read}")
            return redirect('messages')

    if chat_group_id:
        try:
            selected_chat_group = ChatGroup.objects.get(id=chat_group_id, members=request.user)
            messages = selected_chat_group.messages.order_by('timestamp').all()
        except ChatGroup.DoesNotExist:
            return redirect('messages')

    elif chat_groups.exists():
        # Agregamos impresiones para depuración
        for cg in chat_groups:
            print(f"Chat Group: {cg.name}, Unread Messages: {'Yes' if cg.has_unread_messages else 'No'}")
        selected_chat_group = chat_groups.first()
        messages = selected_chat_group.messages.order_by('timestamp').all()

    # Impresiones para depuración
    for cg in chat_groups:
        print(f"Chat Group: {cg.name}, Unread Messages: {'Yes' if cg.has_unread_messages else 'No'}")

    return render(request, 'messages.html', {
        'chat_groups': chat_groups,
        'chat_form': chat_form,
        'new_chat_form': new_chat_form,
        'selected_chat_group': selected_chat_group,
        'messages': messages,
    })

from django.views.decorators.http import require_POST


@require_POST
@login_required
def create_chat(request):
    form = NewChatForm(request.POST)
    if form.is_valid():
        selected_users = form.cleaned_data['users']

        # Para chats grupales (más de 2 personas incluyendo al usuario actual) el nombre es obligatorio
        if len(selected_users) >= 2:
            if not form.cleaned_data['name']:
                # Si no se proporciona un nombre para un chat grupal, retorna un error
                return JsonResponse({'status': 'error', 'errors': {'name': ['Name is required for group chats.']}}, status=400)

            chat_group = form.save()
            for user in selected_users:
                chat_group.members.add(user)
            chat_group.members.add(request.user)
        else:
            # Para chats de dos personas, se crea un chat sin nombre específico
            chat_group = ChatGroup.get_or_create_chat(request.user, selected_users.first())
        
        return JsonResponse({'status': 'success', 'chat_group_id': chat_group.id, 'chat_group_name': chat_group.name})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    

    
from .models import ChatGroup

@login_required
def get_chat_messages(request, chat_group_id):
    try:
        chat_group = ChatGroup.objects.get(id=chat_group_id, members=request.user)
        messages = chat_group.messages.order_by('timestamp').values('text', 'sender__username', 'timestamp')
        return JsonResponse({'messages': list(messages)})
    except ChatGroup.DoesNotExist:
        return JsonResponse({'error': 'Chat group not found'}, status=404)
    

@login_required
def send_message(request, chat_group_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            message = Message.objects.create(
                chat_group_id=chat_group_id,
                sender=request.user,
                text=text
            )
            print(f"Mensaje creado: {message.text}")

            # Obtener todos los miembros del chat_group, excepto el remitente
            chat_group = ChatGroup.objects.get(id=chat_group_id)
            recipients = chat_group.members.exclude(id=request.user.id)

            # Crear MessageReadStatus y MessageNotification para cada destinatario
            for recipient in recipients:
                MessageReadStatus.objects.create(
                    user=recipient,
                    message=message,
                    is_read=False  # Marcar como no leído
                )
                notification = MessageNotification.objects.create(
                    user=recipient,
                    message=message.text,  # o cualquier otro campo relevante de tu modelo Message
                    is_read=False,
                    created_at=message.timestamp  # Asegúrate de que 'timestamp' es la hora de creación del mensaje
                )
                print(f"Notificación creada para {recipient.username}: {notification.message}")

            return JsonResponse({'status': 'success', 'message': {
                'text': message.text,
                'sender_username': request.user.username,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }})
        else:
            return JsonResponse({'status': 'error', 'error': 'Empty message'}, status=400)
    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)



@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    chat_group = ChatGroup.get_or_create_chat(request.user, other_user)

    return redirect('messages_with_id', chat_group_id=chat_group.id)
    return redirect(messages_url)


@login_required
def join_chat_group(request, chat_group_id):
    chat_group = get_object_or_404(ChatGroup, id=chat_group_id)
    chat_group.members.add(request.user)

    return redirect('messages_with_id', chat_group_id=chat_group.id)
    return redirect(messages_url)



@login_required
def get_chat_group_info(request, chat_group_id):
    try:
        chat_group = ChatGroup.objects.get(id=chat_group_id, members=request.user)
        member_count = chat_group.members.count()
        return JsonResponse({
            'member_count': member_count,
            'is_two_person_chat': member_count == 2
        })
    except ChatGroup.DoesNotExist:
        return JsonResponse({'error': 'Chat group not found'}, status=404)
    



@login_required
def chat_action(request, chat_group_id):
    chat_group = get_object_or_404(ChatGroup, id=chat_group_id)

    if request.method == 'POST':
        if chat_group.is_two_person_chat():
            # En el caso de un chat de dos personas, borra solo para el usuario actual.
            chat_group.members.remove(request.user)
            action = 'deleted'
        else:
            # En el caso de un grupo, el usuario abandona el grupo.
            chat_group.members.remove(request.user)
            action = 'left'

            # Si el grupo queda vacío, eliminarlo.
            if chat_group.members.count() == 0:
                chat_group.delete()

        return JsonResponse({'status': 'success', 'action': action})

    return JsonResponse({'status': 'error'}, status=400)



@login_required
def get_chat_group_members(request, chat_group_id):
    chat_group = get_object_or_404(ChatGroup, id=chat_group_id)

    # Asegurarse de que el usuario es miembro del grupo
    if request.user not in chat_group.members.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    members = [
    {
        'username': member.username,
        'profile_url': reverse('profile', args=[member.username])
    }
    for member in chat_group.members.all()
]
    print("Members in group:", list(members))  # Agregar esta línea
    return JsonResponse({'members': list(members)})


@login_required
def mark_messages_as_read(request, chat_group_id):
    if request.method == 'POST':
        # Obtener el grupo de chat
        chat_group = get_object_or_404(ChatGroup, id=chat_group_id, members=request.user)

        # Imprimir para depuración
        print(f"Marcando como leídos los mensajes del grupo de chat {chat_group_id} para el usuario {request.user.username}")

        # Obtener y actualizar el estado de los mensajes a leído
        unread_messages = MessageReadStatus.objects.filter(
            user=request.user,
            message__chat_group=chat_group,
            is_read=False
        )
        
        # Imprimir cantidad de mensajes no leídos para depuración
        print(f"Se encontraron {unread_messages.count()} mensajes no leídos.")

        # Actualizar mensajes a leído
        unread_messages.update(is_read=True)

        # Confirmar acción para depuración
        print(f"Mensajes marcados como leídos.")

        return JsonResponse({'status': 'success'})

    # Mensaje de error si el método no es POST
    print("Error: Método de solicitud no es POST.")
    return JsonResponse({'status': 'error'}, status=400)