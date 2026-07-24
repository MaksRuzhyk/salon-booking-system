from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=155)
    last_name = forms.CharField(max_length=155)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Користувач із такою електронною адресою вже існує.'
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    photo = forms.ImageField(required=False, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg', 'webp'])])
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        duplicate = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)

        if duplicate.exists():
            raise forms.ValidationError(
                'Ця електронна адреса вже використовується.'
            )

        return email

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')

        if photo and photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                'Розмір фотографії не повинен перевищувати 5 МБ.'
            )

        return photo