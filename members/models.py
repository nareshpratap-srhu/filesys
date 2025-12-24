from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import BaseUserManager
import re
from django.core.validators import RegexValidator
from django.db.models.functions import Lower

class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, full_name, password, **extra_fields)
    
class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_departments'
    )

    def __str__(self):
        return self.name


class Designation(models.Model):
    title = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_designations'
    )

    def __str__(self):
        return self.title
    
class Ward(models.Model):
    ward_name = models.CharField(max_length=255, unique=True)
    ward_abbre = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_wards'
    )

    def __str__(self):
        return self.ward_name

class CustomUser(AbstractUser):

    username = None  # Remove default username field    
    email = models.EmailField(unique=True)   # Set email as the unique identifier
    full_name = models.CharField(max_length=255)  
    employee_id = models.CharField(max_length=100, blank=True, null=True)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    department_other = models.CharField(
        max_length=255,
        blank=True,
        help_text="If you select ‘Others’ above, specify here."
    )

    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    ward_other = models.CharField(
        max_length=255,
        blank=True,
        help_text="If you select ‘Others’ above, specify here."
    )

    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    designation_other = models.CharField(
        max_length=255,
        blank=True,
        help_text="If you select ‘Others’ above, specify here."
    )

    # Phone Fields is so setup that it takes all digits and sumbol + and -
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\-\s]+$', # Only digits, plus and hyphen allowed
        message="Phone number may start with '+', and contain only digits, spaces, and hyphens."
    )

    phone = models.CharField(
        validators=[phone_regex],
        max_length=20,  # You can adjust max_length as needed
        blank=True,
        null=True
    )

    # Approval fields
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    # Fields for tracking failed login attempts
    failed_attempts = models.PositiveIntegerField(default=0)

    # ✅ Link the custom manager
    objects = CustomUserManager()

    # Set email as primary identifier
    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['full_name']  # 3️⃣ Full Name is required during registration

    def clean(self):
        """4️⃣ Ensure email is stored in lowercase and is unique (case-insensitive)."""
        self.email = self.email.lower()  # Normalize email to lowercase
        
        # Check for case-insensitive uniqueness
        if CustomUser.objects.filter(email__iexact=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({"email": _("A user with this email already exists.")})

    def save(self, *args, **kwargs):
        """Normalize email, parse full_name into first_name and last_name with salutation handling."""
        self.full_clean()  # Validate model fields

        # Define common salutations (case-insensitive, with and without periods)
        salutations = {"mr", "mr.", "ms", "ms.", "mrs", "mrs.", "dr", "dr.", "prof", "prof."}

        name_parts = self.full_name.strip().split()
        first_name = ""
        last_name = ""

        if name_parts:
            # Normalize the first part to check for salutation
            first = name_parts[0].lower().rstrip(".")
            if first in salutations and len(name_parts) > 1:
                # Include salutation and actual first name in first_name
                first_name = f"{name_parts[0]} {name_parts[1]}"
                last_name = " ".join(name_parts[2:]) if len(name_parts) > 2 else ""
            else:
                # No salutation, just normal split
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        self.first_name = first_name
        self.last_name = last_name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email  # Return email as the string representation
    
    def lock_account(self):
        """Lock the account by setting is_active to False."""
        self.is_active = False
        self.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='unique_lower_email'
            )
        ]
        
class CustomTag(models.Model):
    TAG_TYPE_CHOICES = [
        ('Universal', 'Universal'),
        ('Geo-Pic', 'Geo-Pic'),
        ('File Only', 'File Only'),
    ]
    name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=50, unique=True)  # Abbreviation field (optional)
    value = models.CharField(max_length=255, unique=True, editable=False)
    is_deleted = models.BooleanField(default=False)  # is_deleted field (default is False)
    type = models.CharField(max_length=20, choices=TAG_TYPE_CHOICES, default='Universal')

    def save(self, *args, **kwargs):
        # Remove non-alphanumeric characters and join the parts
        sanitized = re.sub(r'[^A-Za-z0-9]', '', self.name)
        self.value = sanitized
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    




    