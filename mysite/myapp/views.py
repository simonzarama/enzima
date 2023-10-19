from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from .forms import CreateCommunityForm
from django.shortcuts import get_object_or_404
from .models import Community
from django.http import Http404
from .models import Post
from .forms import CreatePostForm
from .models import User
from django.shortcuts import HttpResponse
from .models import Post, Community

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
            # Aquí puedes agregar la lógica de autenticación (lo cubriremos más adelante)
            return redirect('home') # Redirige a la página de inicio después de iniciar sesión
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def home(request):
    return render(request, 'home.html')


@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def cart(request):
    return render(request, 'cart.html')

def notifications(request):
    return render(request, 'notifications.html')


def messages(request):
    return render(request, 'messages.html')

def explore(request):
    # Tu lógica aquí
    return render(request, 'explore.html')


def create_community_view(request):
    if request.method == 'POST':
        form = CreateCommunityForm(request.POST)
        if form.is_valid():
            community = form.save()
            return redirect('view_community', community_name=community.name)
    else:
        form = CreateCommunityForm()

    context = {'form': form}
    return render(request, 'create_community.html', context)



def view_community(request, community_name):
    # Obtén la comunidad basada en el nombre provisto en la URL.
    community = get_object_or_404(Community, name=community_name)
    
    # Obtén los posts relacionados con esta comunidad.
    posts = Post.objects.filter(community=community)
    
    # Renderiza la plantilla con los posts como contexto.
    return render(request, 'view_community.html', {'posts': posts, 'community': community})


def create_post_view(request, community_id):
    if request.method == 'POST':
        title = request.POST.get('post_title')
        content = request.POST.get('post_text')
        community = get_object_or_404(Community, id=community_id)


        # Asegurarse de que request.user está autenticado y obtener la instancia real de User
        if request.user.is_authenticated:
            user_instance = User.objects.get(id=request.user.id)
            post = Post(user=user_instance, title=title, content=content, community=community)
            post.save()

            return redirect('view_community', community_name=community.name)
    return render(request, 'create_post.html')

@login_required
def create_post_view(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    
    if request.method == 'POST':
        form = CreatePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.user = request.user  # Aseguramos que el usuario autenticado es el autor del post
            post.save()
            return redirect('view_community', community_name=community.name)
    else:
        form = CreatePostForm()

    return render(request, 'create_post.html', {'form': form, 'community': community})





