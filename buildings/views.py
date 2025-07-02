from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Building, Apartment
from users.models import User
from .forms import BuildingForm, ApartmentForm

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

@login_required
def get_apartments_by_building(request, building_id):
    """API endpoint to get apartments for a specific building"""
    building = get_object_or_404(Building, id=building_id)
    apartments = Apartment.objects.filter(building=building)
    
    # Serialize apartments to JSON
    data = []
    for apartment in apartments:
        data.append({
            'id': apartment.id,
            'number': str(apartment),
            'floor': apartment.floor,
            'block': apartment.block or '',
            'is_occupied': apartment.is_occupied
        })
    
    return JsonResponse(data, safe=False)
