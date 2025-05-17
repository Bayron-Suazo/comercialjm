from django.urls import path
from django.contrib import admin
from registration import views

urlpatterns = [
        path('login/', views.CustomLoginView.as_view(), name='login'),
    ]
