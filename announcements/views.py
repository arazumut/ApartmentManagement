from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Announcement, AnnouncementRead
from buildings.models import Building


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    
    def get_queryset(self):
        # Admin can see all announcements, residents see only their building's
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Announcement.objects.all()
        else:
            # Get announcements for the user's building
            try:
                return Announcement.objects.filter(building=user.apartment.building, is_active=True)
            except:
                return Announcement.objects.none()


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'announcements/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the user has read this announcement
        announcement = self.get_object()
        user = self.request.user
        context['has_read'] = AnnouncementRead.objects.filter(
            announcement=announcement, 
            user=user
        ).exists()
        return context


class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = ['building', 'title', 'content', 'priority', 'attachment', 'is_active']
    success_url = reverse_lazy('announcement_list')
    
    def test_func(self):
        # Only staff or admin can create announcements
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Announcement created successfully'))
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = ['building', 'title', 'content', 'priority', 'attachment', 'is_active']
    success_url = reverse_lazy('announcement_list')
    
    def test_func(self):
        # Only staff or admin can update announcements
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def form_valid(self, form):
        messages.success(self.request, _('Announcement updated successfully'))
        return super().form_valid(form)


class ResidentAnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/resident_announcement_list.html'
    context_object_name = 'announcements'
    
    def get_queryset(self):
        # Get announcements for the user's building
        user = self.request.user
        try:
            return Announcement.objects.filter(building=user.apartment.building, is_active=True)
        except:
            return Announcement.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Add read status for each announcement
        for announcement in context['announcements']:
            announcement.has_read = AnnouncementRead.objects.filter(
                announcement=announcement, 
                user=user
            ).exists()
        return context


class ReadAnnouncementView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        
        # Mark as read if not already
        AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            user=user
        )
        
        messages.success(request, _('Announcement marked as read'))
        return redirect('announcement_detail', pk=pk)
