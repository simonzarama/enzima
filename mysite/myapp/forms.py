from django import forms
from .models import Community
from django.contrib.auth.models import User
from .models import Post
from .models import CrowdfundingCampaign
from django_select2 import forms as s2forms
from .models import CrowdfundingCampaign, Community
from .models import Resource

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']



class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Correo electrónico'}),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cd['password2']

class CreateCommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'community_type']

class CreatePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'media_file']



from django_select2.forms import Select2MultipleWidget

class CrowdfundingCampaignForm(forms.ModelForm):
    class Meta:
        model = CrowdfundingCampaign
        fields = ['title', 'description', 'goal', 'communities', 'media_file']
        widgets = {
            'communities': Select2MultipleWidget,
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'tags']