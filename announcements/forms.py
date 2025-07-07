from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from .models import Announcement, AnnouncementCategory, AnnouncementTemplate, AnnouncementComment
from buildings.models import Building, Apartment


class AnnouncementForm(forms.ModelForm):
    """Enhanced form for creating/editing announcements"""
    
    class Meta:
        model = Announcement
        fields = [
            'building', 'category', 'title', 'short_description', 'content',
            'announcement_type', 'priority', 'status', 'image', 'attachment',
            'target_groups', 'target_apartments', 'publish_at', 'expires_at',
            'allow_comments', 'is_pinned', 'is_urgent', 'send_notification',
            'send_email', 'send_sms', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Duyuru başlığını girin...')
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Kısa açıklama (önizleme için)...')
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': _('Duyuru içeriğini girin...')
            }),
            'building': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'announcement_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'target_groups': forms.CheckboxSelectMultiple(),
            'target_apartments': forms.CheckboxSelectMultiple(),
            'publish_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_notification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Etiketler (virgülle ayırın)...')
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter buildings based on user permissions
        if user and not (user.is_staff or user.is_superuser):
            if hasattr(user, 'apartment') and user.apartment:
                self.fields['building'].queryset = Building.objects.filter(
                    id=user.apartment.building.id
                )
            else:
                self.fields['building'].queryset = Building.objects.none()
        
        # Filter categories
        self.fields['category'].queryset = AnnouncementCategory.objects.filter(is_active=True)
        
        # Filter apartments based on selected building
        if self.instance.pk and self.instance.building:
            self.fields['target_apartments'].queryset = Apartment.objects.filter(
                building=self.instance.building
            )
        else:
            self.fields['target_apartments'].queryset = Apartment.objects.none()
    
    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        publish_at = self.cleaned_data.get('publish_at')
        
        if expires_at and publish_at and expires_at <= publish_at:
            raise ValidationError(_('Son geçerlilik tarihi yayın tarihinden sonra olmalıdır.'))
        
        return expires_at
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            if isinstance(tags, str):
                # Convert comma-separated string to list
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                return tag_list
        return []


class AnnouncementCategoryForm(forms.ModelForm):
    """Form for managing announcement categories"""
    
    class Meta:
        model = AnnouncementCategory
        fields = ['name', 'slug', 'description', 'color', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Kategori adı...')
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('URL slug...')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Kategori açıklaması...')
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('ri-notification-line')
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AnnouncementTemplateForm(forms.ModelForm):
    """Form for managing announcement templates"""
    
    class Meta:
        model = AnnouncementTemplate
        fields = [
            'name', 'category', 'title_template', 'content_template',
            'priority', 'auto_send_notification', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Şablon adı...')
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Başlık şablonu...')
            }),
            'content_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': _('İçerik şablonu...')
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'auto_send_notification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AnnouncementCategory.objects.filter(is_active=True)


class AnnouncementCommentForm(forms.ModelForm):
    """Form for posting comments on announcements"""
    
    class Meta:
        model = AnnouncementComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Yorumunuzu yazın...')
            })
        }


class AnnouncementFilterForm(forms.Form):
    """Form for filtering announcements"""
    
    category = forms.ModelChoiceField(
        queryset=AnnouncementCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm kategoriler'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', _('Tüm öncelikler'))] + Announcement.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', _('Tüm durumlar'))] + Announcement.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    announcement_type = forms.ChoiceField(
        choices=[('', _('Tüm türler'))] + Announcement.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        empty_label=_('Tüm binalar'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    read_status = forms.ChoiceField(
        choices=[
            ('', _('Tümü')),
            ('read', _('Okunmuş')),
            ('unread', _('Okunmamış'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Başlık veya içerik ara...')
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hide building filter for residents
        if user and not (user.is_staff or user.is_superuser):
            del self.fields['building']
            del self.fields['status']


class BulkAnnouncementForm(forms.Form):
    """Form for bulk operations on announcements"""
    
    ACTION_CHOICES = [
        ('', _('Eylem seçin...')),
        ('publish', _('Yayınla')),
        ('archive', _('Arşivle')),
        ('delete', _('Sil')),
        ('send_notification', _('Bildirim gönder')),
        ('pin', _('Sabitle')),
        ('unpin', _('Sabitlemeyi kaldır')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    announcement_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_announcement_ids(self):
        ids = self.cleaned_data.get('announcement_ids')
        if ids:
            try:
                return [int(id) for id in ids.split(',')]
            except ValueError:
                raise ValidationError(_('Geçersiz duyuru ID\'leri'))
        return []


class AnnouncementQuickCreateForm(forms.Form):
    """Quick form for creating announcements from templates"""
    
    template = forms.ModelChoiceField(
        queryset=AnnouncementTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Başlığı özelleştir (opsiyonel)...')
        })
    )
    
    additional_content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Ek içerik (opsiyonel)...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter buildings based on user permissions
        if user and not (user.is_staff or user.is_superuser):
            if hasattr(user, 'apartment') and user.apartment:
                self.fields['building'].queryset = Building.objects.filter(
                    id=user.apartment.building.id
                )
            else:
                self.fields['building'].queryset = Building.objects.none()
