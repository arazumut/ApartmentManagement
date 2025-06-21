from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Building
from users.models import User

# Create your views here.

class BuildingCreateView(LoginRequiredMixin, CreateView):
    model = Building
    template_name = 'buildings/building_form.html'
    fields = ['name', 'address', 'block_count', 'floors_per_block', 'apartments_per_floor']
    success_url = reverse_lazy('building_list')
    
    def form_valid(self, form):
        # Set admin to current user if they are an admin
        if self.request.user.role == User.ADMIN:
            form.instance.admin = self.request.user
        return super().form_valid(form)

class BuildingDetailView(LoginRequiredMixin, DetailView):
    model = Building
    template_name = 'buildings/building_detail.html'
    context_object_name = 'building'
