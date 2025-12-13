from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from .models import User
from .decorators import role_required


class ProfileView(DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user


class ProfileEditView(UpdateView):
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil muvaffaqiyatli yangilandi.')
        return super().form_valid(form)
