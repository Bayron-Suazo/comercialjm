from django.views.generic import CreateView, View
from django.views.generic.edit import UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User, Group
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import render
from django import forms
from .models import Profile
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.urls import reverse



# ------------------ LOGIN PERSONALIZADO ------------------



class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse('check_profile')

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(username=username)
            profile, _ = Profile.objects.get_or_create(user=user_obj)

            if not user_obj.is_active:
                messages.error(request, "Tu cuenta ha sido bloqueada. Contáctese con el administrador")
                return self.form_invalid(self.get_form())


            user_auth = authenticate(request, username=username, password=password)

            if user_auth is not None:
                profile.failed_attempts = 0
                profile.save()
                login(request, user_auth)
                return redirect(self.get_success_url())
            else:
                profile.failed_attempts += 1
                profile.save()

                if profile.failed_attempts >= 3:
                    user_obj.is_active = False
                    user_obj.save()
                    messages.error(request, "Tu cuenta ha sido bloqueada por intentos fallidos. Contáctese con el administrador")
                else:
                    remaining = 3 - profile.failed_attempts
                    messages.error(request, f"Contraseña incorrecta. Intentos restantes: {remaining}.")

        except User.DoesNotExist:
            messages.error(request, "Usuario o contraseña incorrectos.")

        return self.form_invalid(self.get_form())