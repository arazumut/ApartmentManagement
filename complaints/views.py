from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Complaint, ComplaintComment
from buildings.models import Building, Apartment


class ComplaintListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Complaint
    template_name = 'complaints/complaint_list.html'
    context_object_name = 'complaints'
    
    def test_func(self):
        # Only staff or admin can view all complaints
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        return Complaint.objects.all()


class ComplaintDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Complaint
    template_name = 'complaints/complaint_detail.html'
    context_object_name = 'complaint'
    
    def test_func(self):
        complaint = self.get_object()
        user = self.request.user
        # Staff, admin, the creator, or the assigned person can view
        return (user.is_staff or user.is_superuser or 
                user == complaint.created_by or 
                user == complaint.assigned_to)


class ComplaintCreateView(LoginRequiredMixin, CreateView):
    model = Complaint
    template_name = 'complaints/complaint_form.html'
    fields = ['building', 'apartment', 'title', 'description', 'category', 'attachment']
    success_url = reverse_lazy('resident_complaint_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        # Filter apartments by user's building
        try:
            if hasattr(user, 'apartment') and user.apartment:
                form.fields['building'].initial = user.apartment.building
                form.fields['building'].disabled = True
                form.fields['apartment'].queryset = Apartment.objects.filter(building=user.apartment.building)
                form.fields['apartment'].initial = user.apartment
        except:
            # If user doesn't have an apartment, show all buildings
            pass
        
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Complaint submitted successfully'))
        return super().form_valid(form)


class ComplaintUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Complaint
    template_name = 'complaints/complaint_form.html'
    context_object_name = 'complaint'
    success_url = reverse_lazy('complaint_list')
    
    def test_func(self):
        # Only staff or admin can update complaints
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_form_class(self):
        # Different fields for admin and residents
        if self.request.user.is_staff or self.request.user.is_superuser:
            self.fields = ['status', 'priority', 'assigned_to', 'resolution_notes']
        else:
            self.fields = ['title', 'description', 'category', 'attachment']
        return super().get_form_class()
    
    def form_valid(self, form):
        # If status is changing to resolved, update resolved_at
        if 'status' in form.changed_data and form.cleaned_data['status'] == Complaint.RESOLVED:
            form.instance.resolved_at = timezone.now()
        
        messages.success(self.request, _('Complaint updated successfully'))
        return super().form_valid(form)


class ResidentComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'complaints/resident_complaint_list.html'
    context_object_name = 'complaints'
    
    def get_queryset(self):
        # Show only complaints created by this user
        return Complaint.objects.filter(created_by=self.request.user)


class CaretakerComplaintListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Complaint
    template_name = 'complaints/caretaker_complaint_list.html'
    context_object_name = 'complaints'
    
    def test_func(self):
        # Only caretakers can access this view
        return hasattr(self.request.user, 'is_caretaker') and self.request.user.is_caretaker
    
    def get_queryset(self):
        # Show complaints assigned to this caretaker
        return Complaint.objects.filter(assigned_to=self.request.user)


class AddCommentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        complaint = get_object_or_404(Complaint, pk=self.kwargs['pk'])
        user = self.request.user
        # Only staff, admin, the creator, or the assigned person can add comments
        return (user.is_staff or user.is_superuser or 
                user == complaint.created_by or 
                user == complaint.assigned_to)
    
    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        comment_text = request.POST.get('comment', '')
        
        if comment_text:
            ComplaintComment.objects.create(
                complaint=complaint,
                user=request.user,
                comment=comment_text,
                attachment=request.FILES.get('attachment', None)
            )
            messages.success(request, _('Comment added successfully'))
        
        return redirect('complaint_detail', pk=pk)
