from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
import json
import csv

from .models import (
    Announcement, AnnouncementCategory, AnnouncementTemplate,
    AnnouncementRead, AnnouncementComment, AnnouncementLike,
    AnnouncementView, AnnouncementShare, AnnouncementFeedback,
    get_announcement_statistics
)
from buildings.models import Building


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related(
            'building', 'category', 'created_by'
        ).prefetch_related('reads', 'comments', 'likes')
        
        # Filter by user permissions
        if user.is_staff or user.is_superuser:
            queryset = queryset.all()
        else:
            # Get announcements for user's building
            try:
                if hasattr(user, 'apartment') and user.apartment:
                    queryset = queryset.filter(
                        building=user.apartment.building,
                        status='published'
                    )
                else:
                    queryset = queryset.none()
            except:
                queryset = queryset.none()
        
        # Apply filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(short_description__icontains=search)
            )
        
        building = self.request.GET.get('building')
        if building and (user.is_staff or user.is_superuser):
            queryset = queryset.filter(building_id=building)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by status for staff
        if user.is_staff or user.is_superuser:
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)
        
        return queryset.order_by('-is_pinned', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add categories for filtering
        context['categories'] = AnnouncementCategory.objects.filter(is_active=True)
        
        # Add buildings for staff
        if user.is_staff or user.is_superuser:
            context['buildings'] = Building.objects.all()
        
        # Add read status for each announcement
        if user.is_authenticated:
            read_ids = AnnouncementRead.objects.filter(
                user=user,
                announcement__in=context['announcements']
            ).values_list('announcement_id', flat=True)
            
            for announcement in context['announcements']:
                announcement.is_read_by_user = announcement.id in read_ids
        
        # Add filter parameters
        context['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'priority': self.request.GET.get('priority', ''),
            'search': self.request.GET.get('search', ''),
            'building': self.request.GET.get('building', ''),
            'status': self.request.GET.get('status', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
        }
        
        return context


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'announcements/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related(
            'building', 'category', 'created_by'
        ).prefetch_related('reads', 'comments__user', 'likes')
        
        # Filter by user permissions
        if not (user.is_staff or user.is_superuser):
            try:
                if hasattr(user, 'apartment') and user.apartment:
                    queryset = queryset.filter(
                        building=user.apartment.building,
                        status='published'
                    )
                else:
                    queryset = queryset.none()
            except:
                queryset = queryset.none()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        announcement = self.get_object()
        
        # Track view
        self.track_view(announcement, user)
        
        # Check if user has read this announcement
        context['has_read'] = AnnouncementRead.objects.filter(
            announcement=announcement,
            user=user
        ).exists()
        
        # Check if user has liked this announcement
        context['has_liked'] = AnnouncementLike.objects.filter(
            announcement=announcement,
            user=user
        ).exists()
        
        # Get comments
        if announcement.allow_comments:
            context['comments'] = announcement.comments.filter(
                is_approved=True,
                parent=None
            ).order_by('-created_at')
        
        # Get statistics
        context['stats'] = {
            'total_views': announcement.view_count,
            'total_reads': announcement.read_count,
            'total_likes': announcement.likes.count(),
            'total_comments': announcement.comments.filter(is_approved=True).count(),
            'read_percentage': announcement.get_read_percentage(),
        }
        
        # Related announcements
        context['related_announcements'] = Announcement.objects.filter(
            building=announcement.building,
            status='published'
        ).exclude(id=announcement.id)[:5]
        
        return context
    
    def track_view(self, announcement, user):
        """Track announcement view"""
        # Get client IP
        ip = self.get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        referer = self.request.META.get('HTTP_REFERER', '')
        
        # Create view record
        AnnouncementView.objects.create(
            announcement=announcement,
            user=user if user.is_authenticated else None,
            ip_address=ip,
            user_agent=user_agent,
            referer=referer
        )
        
        # Increment view count
        announcement.increment_view_count()
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = [
        'building', 'category', 'title', 'short_description', 'content',
        'announcement_type', 'priority', 'status', 'image', 'attachment',
        'target_groups', 'target_apartments', 'publish_at', 'expires_at',
        'allow_comments', 'is_pinned', 'is_urgent', 'send_notification',
        'send_email', 'send_sms', 'tags'
    ]
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = AnnouncementTemplate.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Duyuru başarıyla oluşturuldu'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('announcement_detail', kwargs={'pk': self.object.pk})


class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = [
        'building', 'category', 'title', 'short_description', 'content',
        'announcement_type', 'priority', 'status', 'image', 'attachment',
        'target_groups', 'target_apartments', 'publish_at', 'expires_at',
        'allow_comments', 'is_pinned', 'is_urgent', 'send_notification',
        'send_email', 'send_sms', 'tags'
    ]
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('Duyuru başarıyla güncellendi'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('announcement_detail', kwargs={'pk': self.object.pk})


class ResidentAnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/resident_announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 12
    
    def get_queryset(self):
        user = self.request.user
        try:
            if hasattr(user, 'apartment') and user.apartment:
                queryset = Announcement.objects.filter(
                    building=user.apartment.building,
                    status='published'
                ).select_related('category', 'created_by').prefetch_related('reads')
            else:
                queryset = Announcement.objects.none()
        except:
            queryset = Announcement.objects.none()
        
        # Apply filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search)
            )
        
        # Filter by read status
        read_status = self.request.GET.get('read_status')
        if read_status == 'unread':
            read_ids = AnnouncementRead.objects.filter(
                user=user
            ).values_list('announcement_id', flat=True)
            queryset = queryset.exclude(id__in=read_ids)
        elif read_status == 'read':
            read_ids = AnnouncementRead.objects.filter(
                user=user
            ).values_list('announcement_id', flat=True)
            queryset = queryset.filter(id__in=read_ids)
        
        return queryset.order_by('-is_pinned', '-publish_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add categories for filtering
        context['categories'] = AnnouncementCategory.objects.filter(is_active=True)
        
        # Add read status for each announcement
        if user.is_authenticated:
            read_ids = AnnouncementRead.objects.filter(
                user=user,
                announcement__in=context['announcements']
            ).values_list('announcement_id', flat=True)
            
            for announcement in context['announcements']:
                announcement.is_read_by_user = announcement.id in read_ids
        
        # Add statistics
        if hasattr(user, 'apartment') and user.apartment:
            total_announcements = Announcement.objects.filter(
                building=user.apartment.building,
                status='published'
            ).count()
            
            read_announcements = AnnouncementRead.objects.filter(
                user=user,
                announcement__building=user.apartment.building
            ).count()
            
            context['stats'] = {
                'total': total_announcements,
                'read': read_announcements,
                'unread': total_announcements - read_announcements,
                'read_percentage': (read_announcements / total_announcements * 100) if total_announcements > 0 else 0
            }
        
        return context


class MarkAnnouncementReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        
        # Check if user has access to this announcement
        if not (user.is_staff or user.is_superuser):
            try:
                if not (hasattr(user, 'apartment') and user.apartment and 
                       announcement.building == user.apartment.building):
                    messages.error(request, _('Bu duyuruya erişim yetkiniz yok'))
                    return redirect('announcement_list')
            except:
                messages.error(request, _('Bu duyuruya erişim yetkiniz yok'))
                return redirect('announcement_list')
        
        # Mark as read
        announcement.mark_as_read_by(user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, _('Duyuru okundu olarak işaretlendi'))
        return redirect('announcement_detail', pk=pk)


class AnnouncementLikeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        
        # Check if user has access to this announcement
        if not (user.is_staff or user.is_superuser):
            try:
                if not (hasattr(user, 'apartment') and user.apartment and 
                       announcement.building == user.apartment.building):
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            except:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Toggle like
        like, created = AnnouncementLike.objects.get_or_create(
            announcement=announcement,
            user=user
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        total_likes = announcement.likes.count()
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': total_likes
        })


class AnnouncementCommentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        
        # Check if comments are allowed
        if not announcement.allow_comments:
            return JsonResponse({'success': False, 'error': 'Comments not allowed'})
        
        # Check if user has access
        if not (user.is_staff or user.is_superuser):
            try:
                if not (hasattr(user, 'apartment') and user.apartment and 
                       announcement.building == user.apartment.building):
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            except:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        
        comment_text = request.POST.get('comment', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if not comment_text:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
        
        # Create comment
        comment = AnnouncementComment.objects.create(
            announcement=announcement,
            user=user,
            comment=comment_text,
            parent_id=parent_id if parent_id else None,
            is_approved=True  # Auto-approve for now
        )
        
        # Render comment HTML
        comment_html = render_to_string('announcements/partials/comment.html', {
            'comment': comment,
            'user': user
        })
        
        return JsonResponse({
            'success': True,
            'comment_html': comment_html,
            'comment_id': comment.id
        })


class AnnouncementShareView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        platform = request.POST.get('platform')
        
        # Check if user has access
        if not (user.is_staff or user.is_superuser):
            try:
                if not (hasattr(user, 'apartment') and user.apartment and 
                       announcement.building == user.apartment.building):
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            except:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Track share
        AnnouncementShare.objects.create(
            announcement=announcement,
            user=user,
            platform=platform
        )
        
        return JsonResponse({'success': True})


class AnnouncementFeedbackView(LoginRequiredMixin, View):
    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = request.user
        
        # Check if user has access
        if not (user.is_staff or user.is_superuser):
            try:
                if not (hasattr(user, 'apartment') and user.apartment and 
                       announcement.building == user.apartment.building):
                    return JsonResponse({'success': False, 'error': 'Access denied'})
            except:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        
        feedback_type = request.POST.get('feedback_type')
        comment = request.POST.get('comment', '')
        
        # Create or update feedback
        feedback, created = AnnouncementFeedback.objects.get_or_create(
            announcement=announcement,
            user=user,
            defaults={
                'feedback_type': feedback_type,
                'comment': comment
            }
        )
        
        if not created:
            feedback.feedback_type = feedback_type
            feedback.comment = comment
            feedback.save()
        
        return JsonResponse({'success': True})


class AnnouncementAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        building_id = request.GET.get('building')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Get statistics
        stats = get_announcement_statistics(
            building_id=building_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return JsonResponse(stats)


class AnnouncementExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        building_id = request.GET.get('building')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Get announcements
        queryset = Announcement.objects.select_related('building', 'category', 'created_by')
        
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="announcements.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Başlık', 'Bina', 'Kategori', 'Öncelik', 'Durum',
            'Görüntülenme', 'Okunma', 'Oluşturan', 'Oluşturulma Tarihi'
        ])
        
        for announcement in queryset:
            writer.writerow([
                announcement.id,
                announcement.title,
                announcement.building.name,
                announcement.category.name if announcement.category else '',
                announcement.get_priority_display(),
                announcement.get_status_display(),
                announcement.view_count,
                announcement.read_count,
                announcement.created_by.get_full_name() if announcement.created_by else '',
                announcement.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


class AnnouncementTemplateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, template_id):
        template = get_object_or_404(AnnouncementTemplate, id=template_id)
        
        return JsonResponse({
            'title_template': template.title_template,
            'content_template': template.content_template,
            'category_id': template.category_id,
            'priority': template.priority,
            'auto_send_notification': template.auto_send_notification
        })


# API Views for mobile app
class AnnouncementAPIView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        
        # Get user's announcements
        try:
            if hasattr(user, 'apartment') and user.apartment:
                announcements = Announcement.objects.filter(
                    building=user.apartment.building,
                    status='published'
                ).select_related('category', 'created_by')[:20]
            else:
                announcements = []
        except:
            announcements = []
        
        # Get read status
        read_ids = []
        if announcements:
            read_ids = list(AnnouncementRead.objects.filter(
                user=user,
                announcement__in=announcements
            ).values_list('announcement_id', flat=True))
        
        # Serialize data
        data = []
        for announcement in announcements:
            data.append({
                'id': announcement.id,
                'title': announcement.title,
                'short_description': announcement.short_description,
                'content': announcement.content,
                'category': {
                    'id': announcement.category.id,
                    'name': announcement.category.name,
                    'color': announcement.category.color,
                    'icon': announcement.category.icon
                } if announcement.category else None,
                'priority': announcement.priority,
                'priority_display': announcement.get_priority_display(),
                'is_urgent': announcement.is_urgent,
                'is_pinned': announcement.is_pinned,
                'publish_at': announcement.publish_at.isoformat(),
                'expires_at': announcement.expires_at.isoformat() if announcement.expires_at else None,
                'image': announcement.image.url if announcement.image else None,
                'attachment': announcement.attachment.url if announcement.attachment else None,
                'view_count': announcement.view_count,
                'read_count': announcement.read_count,
                'is_read': announcement.id in read_ids,
                'created_by': announcement.created_by.get_full_name() if announcement.created_by else None,
                'created_at': announcement.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'announcements': data,
            'total_count': len(data)
        })


@login_required
def announcement_quick_actions(request, pk):
    """Quick actions for announcements"""
    announcement = get_object_or_404(Announcement, pk=pk)
    user = request.user
    
    # Check permissions
    if not (user.is_staff or user.is_superuser):
        try:
            if not (hasattr(user, 'apartment') and user.apartment and 
                   announcement.building == user.apartment.building):
                return JsonResponse({'success': False, 'error': 'Access denied'})
        except:
            return JsonResponse({'success': False, 'error': 'Access denied'})
    
    action = request.POST.get('action')
    
    if action == 'mark_read':
        announcement.mark_as_read_by(user)
        return JsonResponse({'success': True, 'message': 'Marked as read'})
    
    elif action == 'toggle_like':
        like, created = AnnouncementLike.objects.get_or_create(
            announcement=announcement,
            user=user
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': announcement.likes.count()
        })
    
    elif action == 'share':
        platform = request.POST.get('platform', 'copy_link')
        AnnouncementShare.objects.create(
            announcement=announcement,
            user=user,
            platform=platform
        )
        return JsonResponse({'success': True, 'message': 'Shared successfully'})
    
    return JsonResponse({'success': False, 'error': 'Invalid action'})
