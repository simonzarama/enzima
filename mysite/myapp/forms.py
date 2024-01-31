from django import forms
from .models import Community
from django.contrib.auth.models import User
from .models import Post
from .models import CrowdfundingCampaign
from django_select2 import forms as s2forms
from .models import CrowdfundingCampaign, Community
from .models import Resource
from .models import Trial
from dal import autocomplete

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']


from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'personal_link'] 



class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'error_messages': {
                'username': {
                    'max_length': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
                }
            }
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords do not match.')
        return cd['password2']


class CreateCommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name']

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





#DESPUES DEL BREAK



class TrialForm(forms.ModelForm):


    class Meta:
        model = Trial
        fields = ['title', 'description', 'media_file', 'include_crowdfunding', 'goal', 'medical_supervisor', 'communities', 'administrators', 'participation_criteria'] 
        widgets = {
            'administrators': autocomplete.ModelSelect2Multiple(url='user-autocomplete'),  # URL de la vista de autocompletado para administradores
            'medical_supervisor': autocomplete.ModelSelect2(url='user-autocomplete'),  # URL de la vista de autocompletado para supervisor médico
            'communities': autocomplete.ModelSelect2Multiple(url='community-autocomplete'),  # Asume que tienes una vista de autocompletado para comunidades
            'goal': forms.NumberInput(attrs={
                'step': '0.01',  # Permite valores decimales hasta dos dígitos
                'type': 'number',  # Asegura que sea un campo numérico
            }),
            # Elimina las entradas para 'description' y 'participation_criteria'
        }
            


    def clean(self):
        # Tu lógica de validación existente
        cleaned_data = super().clean()
        include_crowdfunding = cleaned_data.get("include_crowdfunding")
        goal = cleaned_data.get("goal")

        if include_crowdfunding and not goal:
            raise forms.ValidationError("Please set a goal for crowdfunding.")

        return cleaned_data

    def save(self, commit=True):
        # Tu lógica de guardado existente
        trial = super().save(commit=False)
        if commit:
            trial.save()
            self.save_m2m()  # Guarda relaciones ManyToMany
        return trial
    


from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['wants_to_apply','meets_requirements', 'message']


class DonationForm(forms.Form):
    amount = forms.DecimalField(label='Enter your donation', max_digits=10, decimal_places=2)
    donor_email = forms.EmailField(label='Email')




from .models import ChatGroup

class GroupChatForm(forms.ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['name', 'members']



class NewChatForm(forms.ModelForm):
    name = forms.CharField(max_length=255, required=False)  # Hacer que el nombre no sea obligatorio
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url='user-autocomplete'),
        required=False,
        label='Add Users'
    )

    class Meta:
        model = ChatGroup
        fields = ['name', 'users']