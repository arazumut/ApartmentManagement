from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


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
    """Custom user model for the apartment management system."""
    
    # User roles
    ADMIN = 'admin'
    RESIDENT = 'resident'
    CARETAKER = 'caretaker'
    
    ROLE_CHOICES = (
        (ADMIN, _('Admin')),
        (RESIDENT, _('Resident')),
        (CARETAKER, _('Caretaker')),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default=RESIDENT)
    profile_picture = models.ImageField(_('profile picture'), upload_to='profile_pics/', blank=True, null=True)
    
    # Use email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_resident(self):
        return self.role == self.RESIDENT
    
    @property
    def is_caretaker(self):
        return self.role == self.CARETAKER
