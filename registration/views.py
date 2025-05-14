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

