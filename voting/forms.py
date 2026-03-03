# voting/forms.py
from __future__ import annotations

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import VoterProfile, District, Constituency


class VoterProfileForm(forms.ModelForm):
    class Meta:
        model = VoterProfile
        fields = ["citizenship_id", "phone", "district", "constituency"]
        widgets = {
            "district": forms.Select(attrs={"class": "form-select"}),
            "constituency": forms.Select(attrs={"class": "form-select"}),
            "citizenship_id": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["district"].queryset = District.objects.order_by("name_en")
        self.fields["constituency"].queryset = Constituency.objects.none()

        # If editing existing profile
        if self.instance and self.instance.district_id:
            self.fields["constituency"].queryset = Constituency.objects.filter(
                district_id=self.instance.district_id
            ).order_by("code")

        # If district is chosen in POST
        district_id = self.data.get("district")
        if district_id:
            try:
                district_id = int(district_id)
                self.fields["constituency"].queryset = Constituency.objects.filter(
                    district_id=district_id
                ).order_by("code")
            except ValueError:
                pass


class RegisterForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean_email(self):
        email = (self.cleaned_data["email"] or "").lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password(self):
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw

    def save(self) -> User:
        email = self.cleaned_data["email"].lower()
        return User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password"],
        )