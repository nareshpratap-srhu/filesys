from datetime import timezone
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os
from django.utils import timezone  
from members.models import CustomTag
from django.conf import settings
from django.core.validators import FileExtensionValidator
import random
import string


def upload_to(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'

    # Use custom_tag or "no-tag"
    tag = instance.custom_tag.value if instance.custom_tag and instance.custom_tag.value else "no-tag"

    # Generate the file name
    filename = f"IP{instance.uhid}{tag}NO{uuid.uuid4().hex[:8]}.{ext}"

    # Build base UHID folder
    uhid_prefix = f"UHID_{instance.uhid}"

    # Determine subfolder with UHID prefix
    if instance.__class__.__name__ == "CapturedImage":
        subfolder = f"{uhid_prefix}_captured_gps_images"
    elif instance.__class__.__name__ == "UploadedFile":
        subfolder = f"{uhid_prefix}_uploaded_pdf_files"
    elif instance.__class__.__name__ == "UploadedImage":
        subfolder = f"{uhid_prefix}_uploaded_gps_images"
    else:
        subfolder = f"{uhid_prefix}_other"

    # Full path: UHID_<number>/UHID_<number>_<subfolder>/<filename>
    return os.path.join(uhid_prefix, subfolder, filename)

class CapturedImage(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="captured_images")  # Associate with user
    uhid = models.PositiveIntegerField()  # Numeric field for UHID
    image_path = models.ImageField(upload_to=upload_to)  # Store the image with the UHID-based folder structure
    folder_path = models.CharField(max_length=255, blank=True, null=True)  # Folder path to store the UHID-based folder location
    custom_tag = models.ForeignKey(CustomTag, null=True, blank=True, on_delete=models.SET_NULL)
    image_size = models.PositiveIntegerField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)  # Capture t  mimestamp

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_by"
    )

    def save(self, *args, **kwargs):
        if not self.folder_path:
            self.folder_path = f"UHID_{self.uhid}/UHID_{self.uhid}_captured_images/"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"UHID: {self.uhid} - {self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class DeletedCapturedImage(models.Model):
    original_id = models.PositiveIntegerField()  # Store original image ID
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    uhid = models.PositiveIntegerField()
    image_path = models.CharField(max_length=255)  # Store path of the deleted image
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    custom_tag = models.CharField(max_length=100, blank=True, null=True)
    image_size = models.PositiveIntegerField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    captured_at = models.DateTimeField(default=timezone.now)
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="deleted_images")
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deleted UHID: {self.uhid} - {self.deleted_by.username} - {self.deleted_at.strftime('%Y-%m-%d %H:%M:%S')}"


class UploadedFile(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="uploaded_files")
    uhid = models.PositiveIntegerField()
    file_path = models.FileField(upload_to=upload_to)
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    custom_tag = models.ForeignKey(CustomTag, null=True, blank=True, on_delete=models.SET_NULL)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # In bytes
    file_type = models.CharField(max_length=100, blank=True, null=True)  # MIME type
    timestamp = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pdf_deleted_by"
    )

    def save(self, *args, **kwargs):
        if not self.folder_path:
            self.folder_path = f"{self.uhid}/uploaded_files/"

        if self.file_path:
            try:
                self.file_size = self.file_path.size
                self.file_type = self.file_path.file.content_type
            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"UHID: {self.uhid} - {self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def filename(self):
        return os.path.basename(self.file_path.name)

class DeletedUploadedFile(models.Model):
    original_id = models.PositiveIntegerField()  # ID of the original UploadedFile
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)  # Who uploaded it
    uhid = models.PositiveIntegerField()
    file_path = models.CharField(max_length=255)  # Store the path to the file
    folder_path = models.CharField(max_length=255, blank=True, null=True)
    custom_tag = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    captured_at = models.DateTimeField(default=timezone.now)  # When it was originally uploaded
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="deleted_uploaded_files")
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deleted UHID: {self.uhid} - {self.deleted_by.username if self.deleted_by else 'Unknown'} - {self.deleted_at.strftime('%Y-%m-%d %H:%M:%S')}"

class UploadedImage(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="uploaded_images")  # Associate with user
    uhid = models.PositiveIntegerField()  # Numeric field for UHID
    image_path = models.ImageField(upload_to=upload_to)  # Store the image with the UHID-based folder structure
    folder_path = models.CharField(max_length=255, blank=True, null=True)  # Folder path to store the UHID-based folder location
    custom_tag = models.ForeignKey(CustomTag, null=True, blank=True, on_delete=models.SET_NULL)  # Custom tag associated with the image
    image_size = models.PositiveIntegerField(blank=True, null=True)  # Size of the image (in bytes)
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the image was uploaded

    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="upload_deleted_by"
    )

    def save(self, *args, **kwargs):
        if not self.folder_path:
            self.folder_path = f"UHID_{self.uhid}/uploaded_images/"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"UHID: {self.uhid} - {self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


def issue_attachment_upload_to(instance, filename):
    return f"issue_attachments/{instance.user.id}/{filename}"

def generate_unique_issue_id(length=6):
    """
    Generate a unique 6-character alphanumeric ID.
    Retries until a non-conflicting ID is found.
    """
    while True:
        new_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not IssueReport.objects.filter(issue_id=new_id).exists():
            return new_id

class IssueReport(models.Model):
    STATUS_CHOICES = [
        ("open", "Action Pending"),
        ("accepted", "Under Process"),
        ("rejected", "Not Feasible"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="issue_reports"
    )

    description = models.TextField(
        "Issue Description", 
        help_text="Describe the issue", 
        blank=False
    )

    attachment = models.FileField(
        upload_to=issue_attachment_upload_to,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Attach an image or PDF (optional, max 10MB)"
    )

    issue_id = models.CharField(
        max_length=6,
        unique=True,
        editable=False,
        default=generate_unique_issue_id
    )

    current_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="open"
    )

    current_status_marked_at = models.DateTimeField(
        default=timezone.now
    )

    admin_remark = models.TextField(
        blank=True, 
        null=True, 
        help_text="Optional remarks from admin"
    )

    is_deleted = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    def save(self, *args, **kwargs):
        if not self.issue_id:
            self.issue_id = generate_unique_issue_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Issue reported by {self.user.email} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
