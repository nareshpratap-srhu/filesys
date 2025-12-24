from datetime import timezone
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os
from django.utils import timezone  
from members.models import CustomTag
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import random
import string


def upload_to(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'

    # Use custom_tag or "no-tag"
    tag = instance.custom_tag.value if getattr(instance, 'custom_tag', None) and instance.custom_tag.value else "no-tag"

    # Get UHID from patient if available
    if hasattr(instance, 'patient') and instance.patient:
        uhid_number = instance.patient.uhid
    elif hasattr(instance, 'uhid'):
        uhid_number = instance.uhid
    else:
        uhid_number = "UNKNOWN"

    # Generate the file name
    filename = f"IP{uhid_number}{tag}NO{uuid.uuid4().hex[:8]}.{ext}"

    # Build base UHID folder
    uhid_prefix = f"UHID_{uhid_number}"

    # Determine subfolder based on class
    class_name = instance.__class__.__name__
    if class_name == "CapturedImage":
        subfolder = f"{uhid_prefix}_captured_gps_images"
    elif class_name == "UploadedFile":
        subfolder = f"{uhid_prefix}_uploaded_pdf_files"
    elif class_name == "UploadedImage":
        subfolder = f"{uhid_prefix}_uploaded_gps_images"
    elif class_name == "OtherUploadedFile":
        subfolder = f"{uhid_prefix}_patient_pdf"
    else:
        subfolder = f"{uhid_prefix}_other"

    # Full path: UHID_<number>/<subfolder>/<filename>
    return os.path.join(uhid_prefix, subfolder, filename)


class EchsPatientMaster(models.Model):
    uhid = models.PositiveIntegerField(unique=True)
    patient_name = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15, null=True, blank=True)
    date_of_admission = models.DateTimeField(null=True, blank=True)
    date_of_discharge = models.DateTimeField(null=True, blank=True)
    created_on= models.DateTimeField(auto_now_add=True)
    created_by= models.ForeignKey(get_user_model(),on_delete=models.SET_NULL,null=True,blank=True,related_name="patients_created")
    updated_on= models.DateTimeField(auto_now=True)
    updated_by= models.ForeignKey(get_user_model(),on_delete=models.SET_NULL,null=True,blank=True,related_name="patients_updated")

    def __str__(self):
        return f"{self.patient_name} (UHID: {self.uhid})"


class CapturedImage(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="echs_captured_images"
    )
    patient = models.ForeignKey(
        EchsPatientMaster,
        on_delete=models.CASCADE,
        related_name="patient_captured_images"
    )
    image_path = models.ImageField(upload_to=upload_to)
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    custom_tag = models.ForeignKey(
        CustomTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='echs_capturedimage_tags'  # UNIQUE
    )
    image_size = models.PositiveIntegerField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="echs_deleted_images"
    )

    def save(self, *args, **kwargs):
        if not self.folder_path:
            self.folder_path = f"UHID_{self.patient.uhid}/UHID_{self.patient.uhid}_captured_gps_images/"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.patient_name} ({self.patient.uhid})"


class UploadedFile(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="echs_uploaded_files"
    )

    patient = models.ForeignKey(
        "EchsPatientMaster",
        on_delete=models.CASCADE,
        related_name="uploaded_files"
    )

    file_path = models.FileField(upload_to=upload_to)
    folder_path = models.CharField(max_length=255, blank=True, null=True)

    custom_tag = models.ForeignKey(
        CustomTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="echs_uploadedfile_tags"
    )

    file_size = models.PositiveIntegerField(blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="echs_deleted_file"
    )

    def save(self, *args, **kwargs):
        # Set folder path if not already set
        if not self.folder_path:
            self.folder_path = f"UHID_{self.patient.uhid}/UHID_{self.patient.uhid}_uploaded_pdf_files/"

        # Store file size/type
        if self.file_path:
            try:
                self.file_size = self.file_path.size
                self.file_type = self.file_path.file.content_type
            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.patient_name} ({self.patient.uhid}) - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def filename(self):
        return os.path.basename(self.file_path.name)


class UploadedImage(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="echs_uploaded_images"   # UNIQUE
    )

    patient = models.ForeignKey(
        "EchsPatientMaster",
        on_delete=models.CASCADE,
        related_name="uploaded_images"        # UNIQUE + Matches UploadedFile pattern
    )

    image_path = models.ImageField(upload_to=upload_to)

    folder_path = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    custom_tag = models.ForeignKey(
        CustomTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="echs_uploadedimage_tags"   # UNIQUE
    )

    image_size = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="delete_uploaded_images"
    )

    def save(self, *args, **kwargs):
        # Automatically assign folder
        if not self.folder_path:
            self.folder_path = f"UHID_{self.patient.uhid}/UHID_{self.patient.uhid}_uploaded_gps_images/"

        # Save image size
        if self.image_path and hasattr(self.image_path, "size"):
            self.image_size = self.image_path.size

        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Unknown User"
        return f"{self.patient.patient_name} ({self.patient.uhid}) - {username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class OtherUploadedFile(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="converted_files"
    )

    patient = models.ForeignKey(
        "EchsPatientMaster",
        on_delete=models.CASCADE,
        related_name="converted_files"
    )

    file_path = models.FileField(upload_to=upload_to)
    folder_path = models.CharField(max_length=255, blank=True, null=True)

    custom_tag = models.ForeignKey(
        CustomTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="converted_files"
    )

    file_size = models.PositiveIntegerField(blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="delete_other_files"
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField(null=True)
    linked_object = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        # Set folder path if not already set
        if not self.folder_path:
            self.folder_path = f"UHID_{self.patient.uhid}/UHID_{self.patient.uhid}_patient_pdf/"


        # Store file size/type
        if self.file_path:
            try:
                self.file_size = self.file_path.size
                self.file_type = self.file_path.file.content_type
            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.patient_name} ({self.patient.uhid}) - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def filename(self):
        return os.path.basename(self.file_path.name)

