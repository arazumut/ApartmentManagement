from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
from PIL import Image
import os


class UserManager(BaseUserManager):
    """Manager for custom user model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a normal user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Enhanced custom user model for the apartment management system."""
    
    # User roles
    ADMIN = 'admin'
    RESIDENT = 'resident'
    CARETAKER = 'caretaker'
    SECURITY = 'security'
    
    ROLE_CHOICES = (
        (ADMIN, _('Yönetici')),
        (RESIDENT, _('Sakin')),
        (CARETAKER, _('Kapıcı')),
        (SECURITY, _('Güvenlik')),
    )
    
    # Phone number validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    # Basic Information
    email = models.EmailField(_('e-posta adresi'), unique=True)
    phone_number = models.CharField(_('telefon numarası'), validators=[phone_regex], max_length=17, blank=True, null=True)
    role = models.CharField(_('rol'), max_length=20, choices=ROLE_CHOICES, default=RESIDENT)
    profile_picture = models.ImageField(_('profil resmi'), upload_to='profile_pics/', blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField(_('doğum tarihi'), null=True, blank=True)
    national_id = models.CharField(_('TC kimlik no'), max_length=11, blank=True, null=True)
    emergency_contact_name = models.CharField(_('acil durum iletişim adı'), max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(_('acil durum telefonu'), validators=[phone_regex], max_length=17, blank=True, null=True)
    
    # Address Information
    address = models.TextField(_('adres'), blank=True, null=True)
    city = models.CharField(_('şehir'), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_('posta kodu'), max_length=10, blank=True, null=True)
    
    # Professional Information (for caretakers/security)
    hire_date = models.DateField(_('işe giriş tarihi'), null=True, blank=True)
    salary = models.DecimalField(_('maaş'), max_digits=10, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(_('istihdam türü'), max_length=20, choices=[
        ('full_time', _('Tam Zamanlı')),
        ('part_time', _('Yarı Zamanlı')),
        ('contract', _('Sözleşmeli')),
        ('temporary', _('Geçici')),
    ], blank=True, null=True)
    
    # Settings and Preferences
    language = models.CharField(_('dil'), max_length=10, choices=[
        ('tr', _('Türkçe')),
        ('en', _('İngilizce')),
    ], default='tr')
    timezone = models.CharField(_('zaman dilimi'), max_length=50, default='Europe/Istanbul')
    
    # Account Status
    is_verified = models.BooleanField(_('doğrulanmış hesap'), default=False)
    email_verified = models.BooleanField(_('e-posta doğrulandı'), default=False)
    phone_verified = models.BooleanField(_('telefon doğrulandı'), default=False)
    
    # Activity Tracking
    last_login_ip = models.GenericIPAddressField(_('son giriş IP'), null=True, blank=True)
    login_count = models.PositiveIntegerField(_('giriş sayısı'), default=0)
    
    # Permissions
    can_create_announcements = models.BooleanField(_('duyuru oluşturabilir'), default=False)
    can_view_financial_reports = models.BooleanField(_('mali raporları görüntüleyebilir'), default=False)
    can_manage_complaints = models.BooleanField(_('şikayetleri yönetebilir'), default=False)
    
    # Use email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Set default permissions based on role
        if self.role == self.ADMIN:
            self.can_create_announcements = True
            self.can_view_financial_reports = True
            self.can_manage_complaints = True
        elif self.role == self.CARETAKER:
            self.can_manage_complaints = True
        
        super().save(*args, **kwargs)
        
        # Resize profile picture if uploaded
        if self.profile_picture:
            self.resize_profile_picture()
    
    def resize_profile_picture(self):
        """Resize profile picture to save storage space"""
        if self.profile_picture:
            img = Image.open(self.profile_picture.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300), Image.LANCZOS)
                img.save(self.profile_picture.path)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_full_name(self):
        return self.full_name or self.email
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_resident(self):
        return self.role == self.RESIDENT
    
    @property
    def is_caretaker(self):
        return self.role == self.CARETAKER
    
    @property
    def is_security(self):
        return self.role == self.SECURITY
    
    @property
    def is_staff_member(self):
        return self.role in [self.CARETAKER, self.SECURITY, self.ADMIN]
    
    def get_age(self):
        """Calculate user's age"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def get_initials(self):
        """Get user's initials"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
        elif self.first_name:
            return self.first_name[0].upper()
        else:
            return self.email[0].upper()
    
    def get_role_display_with_icon(self):
        """Get role display with icon"""
        icons = {
            self.ADMIN: 'fas fa-user-shield',
            self.RESIDENT: 'fas fa-user',
            self.CARETAKER: 'fas fa-tools',
            self.SECURITY: 'fas fa-shield-alt',
        }
        return {
            'display': self.get_role_display(),
            'icon': icons.get(self.role, 'fas fa-user')
        }
    
    def get_apartments(self):
        """Get apartments associated with this user"""
        from buildings.models import Apartment
        return Apartment.objects.filter(models.Q(resident=self) | models.Q(owner=self))
    
    def get_buildings(self):
        """Get buildings associated with this user"""
        from buildings.models import Building
        
        if self.is_admin:
            return Building.objects.filter(admin=self)
        elif self.is_caretaker:
            return Building.objects.filter(caretaker=self)
        elif self.is_resident:
            return Building.objects.filter(apartments__in=self.get_apartments()).distinct()
        else:
            return Building.objects.none()
    
    def can_access_building(self, building):
        """Check if user can access a specific building"""
        if self.is_admin:
            return building.admin == self
        elif self.is_caretaker:
            return building.caretaker == self
        elif self.is_resident:
            return building in self.get_buildings()
        return False
    
    def get_notification_count(self):
        """Get unread notification count"""
        return self.notifications.filter(is_read=False).count()
    
    def get_complaint_count(self):
        """Get complaint count based on role"""
        if self.is_admin or self.is_caretaker:
            return self.assigned_complaints.filter(status__in=['new', 'in_progress']).count()
        else:
            return self.created_complaints.filter(status__in=['new', 'in_progress']).count()
    
    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
        ordering = ['first_name', 'last_name', 'email']


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Social Media
    instagram = models.CharField(_('Instagram'), max_length=100, blank=True, null=True)
    facebook = models.CharField(_('Facebook'), max_length=100, blank=True, null=True)
    twitter = models.CharField(_('Twitter'), max_length=100, blank=True, null=True)
    
    # Personal Preferences
    receive_sms_notifications = models.BooleanField(_('SMS bildirimi al'), default=False)
    receive_email_notifications = models.BooleanField(_('E-posta bildirimi al'), default=True)
    share_contact_info = models.BooleanField(_('İletişim bilgilerini paylaş'), default=True)
    
    # Privacy Settings
    show_profile_to_neighbors = models.BooleanField(_('Profili komşulara göster'), default=True)
    allow_direct_messages = models.BooleanField(_('Doğrudan mesajlara izin ver'), default=True)
    
    # Bio and Description
    bio = models.TextField(_('biyografi'), max_length=500, blank=True, null=True)
    interests = models.CharField(_('ilgi alanları'), max_length=200, blank=True, null=True)
    profession = models.CharField(_('meslek'), max_length=100, blank=True, null=True)
    
    # Family Information
    family_members = models.PositiveIntegerField(_('aile üyesi sayısı'), default=1)
    has_pets = models.BooleanField(_('evcil hayvan var'), default=False)
    pet_details = models.TextField(_('evcil hayvan detayları'), blank=True, null=True)
    
    # Vehicle Information
    has_vehicle = models.BooleanField(_('araç var'), default=False)
    vehicle_details = models.TextField(_('araç detayları'), blank=True, null=True)
    
    # Miscellaneous
    notes = models.TextField(_('notlar'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Profil"
    
    class Meta:
        verbose_name = _('Kullanıcı Profili')
        verbose_name_plural = _('Kullanıcı Profilleri')


class UserActivity(models.Model):
    """Track user activities"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(_('aktivite türü'), max_length=50, choices=[
        ('login', _('Giriş')),
        ('logout', _('Çıkış')),
        ('profile_update', _('Profil Güncelleme')),
        ('password_change', _('Şifre Değiştirme')),
        ('complaint_create', _('Şikayet Oluşturma')),
        ('payment_made', _('Ödeme Yapma')),
        ('announcement_view', _('Duyuru Görüntüleme')),
        ('other', _('Diğer')),
    ])
    description = models.TextField(_('açıklama'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP adresi'), null=True, blank=True)
    user_agent = models.TextField(_('kullanıcı aracısı'), blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()}"
    
    class Meta:
        verbose_name = _('Kullanıcı Aktivitesi')
        verbose_name_plural = _('Kullanıcı Aktiviteleri')
        ordering = ['-timestamp']
