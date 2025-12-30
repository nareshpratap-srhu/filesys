import base64
import uuid
import traceback

from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from echs.models import EchsPatientMaster, CapturedImage, UploadedFile, UploadedImage, OtherUploadedFile
from datetime import datetime
from members.models import CustomTag
from django.db import models
import os
import shutil
import zipfile
import time
from itertools import chain
from operator import attrgetter
from django.utils import timezone
from echs.services import generate_pdf_file
from django.conf import settings
from django.contrib import messages
from django.db.models import Value, CharField
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse




# Only allow superusers to approve other users
def is_super_user(user):
    return user.is_superuser

@login_required
def capture_uhid_camera(request):
    # Define keypad layout
    keypad_rows = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        ["⌫", 0, "✔"]
    ]

    # Calculate last two digits of the current year
    yearPrefix = str(datetime.now().year)[-2:]
    
    # Debug log
    print(f"[DEBUG] Year Prefix calculated: {yearPrefix}")

    return render(request, "echs/capture_uhid_camera.html", {
        "user": request.user,
        "keypad_rows": keypad_rows,
        "yearPrefix": yearPrefix,  # Send to template
    })


#uhid options
def echs_uhid_options(request):
    uhid = request.GET.get('uhid')
    if not uhid:
        return redirect('echs:uhid_capture_camera')  # fallback

    patient_name= None
    file_count=0
    total_image_count=0
    other_files = 0 
    total_deleted_files=0

    try:
        patient = EchsPatientMaster.objects.get(uhid=uhid)
        patient_name = patient.patient_name
        captured_count = patient.patient_captured_images.filter(is_deleted=False).count()
        captured_deleted= patient.patient_captured_images.filter(is_deleted=True, deleted_by_id = request.user.id).count()      

        uploaded_image_count = patient.uploaded_images.filter(is_deleted=False).count()       
        uploaded_deleted = patient.uploaded_images.filter(is_deleted=True, deleted_by_id = request.user.id).count()


        file_count = patient.uploaded_files.filter(is_deleted=False).count() 
        file_deleted = patient.uploaded_files.filter(is_deleted=True, deleted_by_id = request.user.id).count() 

        other_files = patient.converted_files.filter(is_deleted=False).count() 

        total_image_count = captured_count + uploaded_image_count
        total_deleted_files= captured_deleted + uploaded_deleted + file_deleted
    except EchsPatientMaster.DoesNotExist:
        pass
  
    return render(request, 'echs/echs_uhid_options.html', {
        'uhid': uhid,
        'image_count': total_image_count,
        'file_count': file_count,
        'other_files': other_files,
        'deleted_files': total_deleted_files,
        'patient_name': patient_name,
    })


#register patient details
def register_patient(request):
    uhid = request.GET.get("uhid")
    reason = request.GET.get("reason")
    next_url = request.GET.get("next", "/") 

    patient = None  

    if uhid:
        patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if request.method == "POST":
        uhid = request.POST.get("uhid")
        patient_name = request.POST.get("patient_name")
        mobile_no = request.POST.get("mobile_no")
        date_of_admission = request.POST.get("date_of_admission")
        date_of_discharge = request.POST.get("date_of_discharge")

        if date_of_discharge == "" or date_of_discharge is None:
            date_of_discharge = None

        if patient:  
            # UPDATE existing record
            patient.patient_name = patient_name
            patient.mobile_no = mobile_no
            patient.date_of_admission = date_of_admission
            patient.date_of_discharge = date_of_discharge
            patient.updated_by = request.user
            patient.save()
        else:
            # CREATE new record
            EchsPatientMaster.objects.create(
                uhid=uhid,
                patient_name=patient_name,
                mobile_no=mobile_no,
                date_of_admission=date_of_admission,
                date_of_discharge=date_of_discharge,
                created_by=request.user,          
            )

        return redirect(next_url)

    return render(request, "echs/register-patient.html", {
        "uhid": uhid,
        "patient": patient,
        "next": next_url,
        "show_discharge_warning": reason == "discharge_required"
    })


@login_required
def check_discharge_status(request):
    uhid = request.GET.get("uhid")
    tag_id = request.GET.get("tag_id")

    # ✅ Only Discharge tag (ID = 11)
    if str(tag_id) != "11":
        return JsonResponse({"allowed": True})

    patient = get_object_or_404(EchsPatientMaster, uhid=uhid)

    if patient.date_of_discharge:
        return JsonResponse({"allowed": True})
    else:
        return JsonResponse({
            "allowed": False,
            "redirect_url": (
                f"/echs/register_patient/"
                f"?uhid={uhid}"
                f"&reason=discharge_required"
                f"&next=/echs/image_capture/?uhid={uhid}"
            )
        })


@login_required
def echs_image_capture(request):
    uhid = request.GET.get('uhid')

    if not uhid:
        return render(request, "echs/echs_capture_images.html", {
            "uhid": None,
            "patient_name": None,
        })
    
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        # Build next URL (back to capture screen)
        next_url = f"/echs/image_capture/?uhid={uhid}"
        return redirect(f"/echs/register_patient/?uhid={uhid}&next={next_url}")

    # Patient found
    patient_name = patient.patient_name

    # Get available custom tags
    custom_tags = CustomTag.objects.filter(is_deleted=False).order_by('name')
    
    if request.method == "POST":
        image_data = request.POST.get("image_data")
        uhid = request.POST.get("uhid")
        custom_tag = request.POST.get("custom_tag")
        image_size = request.POST.get("image_size")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        print(f"Received UHID: {uhid}")
        print(f"Received Image Data: {image_data[:50]}...")
        print(f"Received Custom Tag: {custom_tag}")
        print(f"Received Image Size: {image_size}")
        print(f"Received Latitude: {latitude}")
        print(f"Received Longitude: {longitude}")

        try:
            # Ensure UHID is a valid integer and within range
            uhid_int = int(uhid)
            if uhid_int > 2147483647 or uhid_int < -2147483648:  # PostgreSQL Integer Range
                raise ValidationError("UHID is too large or invalid!")
            
            patient = EchsPatientMaster.objects.filter(uhid=uhid_int).first()
            if not patient:
                return JsonResponse({"success": False, "error": "Patient not found!"})

            # Process and save image
            format, imgstr = image_data.split(";base64,")
            ext = format.split("/")[-1]
            file_name = f"{uuid.uuid4().hex}.{ext}"
            image_file = ContentFile(base64.b64decode(imgstr), name=file_name)

            # Handle the custom tag
            tag_obj = None
            if custom_tag:
                tag_obj = CustomTag.objects.get(id=custom_tag)

            captured_image = CapturedImage.objects.create(
                user=request.user,
                patient=patient,
                image_path=image_file,
                custom_tag=tag_obj,
                image_size=image_size,
                latitude=latitude,
                longitude=longitude
                )

            if tag_obj and tag_obj.id in [10, 11]:
                generate_pdf_file(patient, captured_image,request.user)


            print("Image successfully saved to database.")
            return JsonResponse({"success": True, "message": "Image uploaded successfully!"})

        except ValueError:
            return JsonResponse({"success": False, "error": "UHID must be a valid number!"})
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e)})
        except Exception as e:
            print("❌ ERROR OCCURRED:", traceback.format_exc())
            return JsonResponse({"success": False, "error": "Something went wrong. Please try again."})

    return render(request, "echs/echs_capture_images.html", 
    {"uhid": uhid, "custom_tags": custom_tags, "patient_name": patient_name, "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY})

MAX_FILE_SIZE = 45 * 1024 * 1024  # 45 MB limit


@login_required
def upload_file_image2image(request):
    uhid = request.GET.get("uhid")
    if not uhid:
        return render(request, "echs/capture_images.html", {
            "uhid": None,
            "patient_name": None,
            "custom_tags": None,
        })

    # 🔍 2. Check if patient exists
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        # Build next URL (redirect back after registration)
        next_url = f"/echs/up_file_image2image/?uhid={uhid}"
        return redirect(f"/echs/register_patient/?uhid={uhid}&next={next_url}")

    # Patient exists → extract name
    patient_name = patient.patient_name
    custom_tags = CustomTag.objects.filter(is_deleted=False).order_by('name')

    if request.method == "POST":
        custom_tag_id = request.POST.get("custom-tag-select")
        uploaded_file = request.FILES.get("file")

        if not custom_tag_id:
            return JsonResponse({"success": False, "error": "Custom tag is required!"})

        if not uploaded_file:
            return JsonResponse({"success": False, "error": "No file uploaded!"})

        file_size = uploaded_file.size
        file_type = uploaded_file.content_type

        print(f"Received UHID (from GET): {uhid}")
        print(f"Received File: {uploaded_file}")
        print(f"Received Custom Tag: {custom_tag_id}")
        print(f"File Size: {file_size} bytes")
        print(f"File Type: {file_type}")

        try:
            # Validate UHID
            uhid_int = int(uhid)
            if uhid_int > 2147483647 or uhid_int < -2147483648:
                raise ValidationError("UHID is out of valid range!")

            # Validate file size
            if file_size > MAX_FILE_SIZE:
                raise ValidationError(f"File size exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit!")

            # Validate file type
            allowed_file_types = ['image/jpeg', 'image/jpg', 'image/png']
            if file_type not in allowed_file_types:
                raise ValidationError("Unsupported file type! Only JPEG and PNG images are allowed.")

            # Validate custom tag
            try:
                tag_obj = CustomTag.objects.get(id=custom_tag_id, is_deleted=False)
            except CustomTag.DoesNotExist:
                raise ValidationError("Invalid custom tag selected.")

            # Save the uploaded file
            uploaded_image = UploadedImage.objects.create(
                user=request.user,
                patient=patient,
                image_path=uploaded_file,
                custom_tag=tag_obj,
                image_size=file_size,
            )

            if tag_obj and tag_obj.id in [10, 11]:
              generate_pdf_file(patient, uploaded_image, request.user)
              
            print("✅ Image successfully uploaded.")
            return JsonResponse({"success": True, "message": "Image uploaded successfully!"})

        except ValueError:
            return JsonResponse({"success": False, "error": "UHID must be a valid number!"})
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e)})
        except Exception:
            print("❌ ERROR OCCURRED:", traceback.format_exc())
            return JsonResponse({"success": False, "error": "Something went wrong. Please try again."})

    return render(request, "echs/upload_file_image2image.html", {
        "uhid": uhid,
        "patient_name": patient_name,
        "custom_tags": custom_tags
    })



@login_required
def upload_file_multi_image2image(request):
    uhid = request.GET.get("uhid")
    
    if not uhid:
        return render(request, "echs/capture_images.html", {
            "uhid": None,
            "patient_name": None,
            "custom_tags": None,
        })

    # 🔍 2. Check if patient exists
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        # Build next URL (redirect back after registration)
        next_url = f"/echs/up_file_multi_image2image/?uhid={uhid}"
        return redirect(f"/echs/register_patient/?uhid={uhid}&next={next_url}")

    # Patient exists → extract name
    patient_name = patient.patient_name
    custom_tags = CustomTag.objects.filter(is_deleted=False).order_by('name')
    
    # patient = EchsPatientMaster.objects.filter(uhid=uhid).first()
    # patient_name = patient.patient_name

    if request.method == "POST":
        custom_tag_id = request.POST.get("custom-tag-select")
        uploaded_files = request.FILES.getlist("files")  # <-- changed here

        # If no tag selected, return immediately
        if not custom_tag_id:
            return JsonResponse({"success": False, "error": "Custom tag is required!"})

        # If no files uploaded at all, error
        if not uploaded_files:
            return JsonResponse({"success": False, "error": "No files uploaded!"})

        # Attempt to fetch/validate the tag object once
        try:
            tag_obj = CustomTag.objects.get(id=custom_tag_id, is_deleted=False)
        except CustomTag.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid custom tag selected."})

        results = []  # collect per-file status

        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_type = uploaded_file.content_type

            print(f"Received UHID (from GET): {uhid}")
            print(f"Received File: {file_name}")
            print(f"Received Custom Tag: {custom_tag_id}")
            print(f"File Size: {file_size} bytes")
            print(f"File Type: {file_type}")

            try:
                # Validate UHID once per request (same for all files)
                uhid_int = int(uhid)
                if uhid_int > 2147483647 or uhid_int < 0:
                    raise ValidationError("UHID is out of valid range!")

                # Validate each file’s size
                if file_size > MAX_FILE_SIZE:
                    raise ValidationError(f"\"{file_name}\" exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit!")

                # Validate each file’s MIME type
                allowed_file_types = ['image/jpeg', 'image/jpg', 'image/png']
                if file_type not in allowed_file_types:
                    raise ValidationError(f"\"{file_name}\" unsupported type! Only JPEG/PNG allowed.")

                # Save this file to the UploadedImage model
                uploaded_image = UploadedImage.objects.create(
                    user=request.user,
                    patient=patient,
                    image_path=uploaded_file,  # Django will assign a unique name under your upload_to
                    custom_tag=tag_obj,
                    image_size=file_size,
                )

                if tag_obj and tag_obj.id in [10, 11]:
                    generate_pdf_file(patient, uploaded_image, request.user)

                print(f"✅ \"{file_name}\" uploaded successfully.")
                results.append({"file": file_name, "success": True})

            except ValueError:
                results.append({"file": file_name, "success": False, "error": "UHID must be a valid number!"})
                # If UHID itself is invalid, break out (all files share same UHID)
                break

            except ValidationError as e:
                results.append({"file": file_name, "success": False, "error": str(e)})
                # Continue to next file—others might still succeed
                continue

            except Exception:
                # Log the traceback, add a generic error for this file
                print("❌ ERROR OCCURRED:", traceback.format_exc())
                results.append({"file": file_name, "success": False, "error": "Unexpected error. Please try again."})
                continue

        # Decide how to report back:
        # - If every entry in results has success=True, overall success.
        # - If any entry has success=False, include those errors.
        all_success = all(r.get("success") for r in results)

        return JsonResponse({
            "success": all_success,
            "results": results
        })

    # GET: render the template as before
    return render(request, "echs/upload_file_multi_image2image.html", {
        "uhid": uhid,
        "patient_name": patient_name,
        "custom_tags": custom_tags
    })



@login_required
def upload_file_image2pdf(request):
    uhid = request.GET.get("uhid")
    
    if not uhid:
        return render(request, "echs/capture_images.html", {
            "uhid": None,
            "patient_name": None,
            "custom_tags": None,
        })

    # 🔍 2. Check if patient exists
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        # Build next URL (redirect back after registration)
        next_url = f"/echs/up_file_image2pdf/?uhid={uhid}"
        return redirect(f"/echs/register_patient/?uhid={uhid}&next={next_url}")

    # Patient exists → extract name
    patient_name = patient.patient_name

    custom_tags = CustomTag.objects.filter(is_deleted=False).order_by('name')

    if request.method == "POST":
        custom_tag_id = request.POST.get("custom-tag-select")
        uploaded_file = request.FILES.get("file")

        if not custom_tag_id:
            return JsonResponse({"success": False, "error": "Custom tag is required!"})

        if not uploaded_file:
            return JsonResponse({"success": False, "error": "No file uploaded!"})

        file_size = uploaded_file.size
        file_type = uploaded_file.content_type

        print(f"Received UHID (from GET): {uhid}")
        print(f"Received File: {uploaded_file}")
        print(f"Received Custom Tag: {custom_tag_id}")
        print(f"File Size: {file_size} bytes")
        print(f"File Type: {file_type}")

        try:
            uhid_int = int(uhid)
            if uhid_int > 2147483647 or uhid_int < -2147483648:
                raise ValidationError("UHID is too large or invalid!")

            if file_size > MAX_FILE_SIZE:
                raise ValidationError(f"File size exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit!")

            allowed_file_types = [
                'application/pdf',
                'image/jpeg',
                'image/jpg',
                'image/png'
            ]
            if file_type not in allowed_file_types:
                raise ValidationError("Unsupported file type! Allowed types: PDF, JPEG, PNG.")

            # ✅ Lookup tag by ID if present
            tag_obj = None
            if custom_tag_id:
                try:
                    tag_obj = CustomTag.objects.get(id=custom_tag_id, is_deleted=False)
                except CustomTag.DoesNotExist:
                    raise ValidationError("Invalid custom tag selected.")

            # Save the uploaded file to the database
            UploadedFile.objects.create(
                user=request.user,
                patient=patient,
                file_path=uploaded_file,
                custom_tag=tag_obj,
                file_size=file_size,
                file_type=file_type
            )

            print("✅ File successfully uploaded.")
            return JsonResponse({"success": True, "message": "File uploaded successfully!"})

        except ValueError:
            return JsonResponse({"success": False, "error": "UHID must be a valid number!"})
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e)})
        except Exception as e:
            print("❌ ERROR OCCURRED:", traceback.format_exc())
            return JsonResponse({"success": False, "error": "Something went wrong. Please try again."})

    return render(request, "echs/upload_file_image2pdf.html", {
        "uhid": uhid,
        "patient_name": patient_name,
        "custom_tags": custom_tags
    })



@login_required
def upload_file_pdf2pdf(request):
    uhid = request.GET.get("uhid")

    if not uhid:
        return render(request, "echs/capture_images.html", {
            "uhid": None,
            "patient_name": None,
            "custom_tags": None,
        })

    # 🔍 2. Check if patient exists
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        # Build next URL (redirect back after registration)
        next_url = f"/echs/up_file_pdf2pdf/?uhid={uhid}"
        return redirect(f"/echs/register_patient/?uhid={uhid}&next={next_url}")

    # Patient exists → extract name
    patient_name = patient.patient_name
    custom_tags = CustomTag.objects.filter(is_deleted=False).order_by('name')

    if request.method == "POST":
        custom_tag_id = request.POST.get("custom-tag-select")
        uploaded_files = request.FILES.getlist("files")  # Get a list of PDFs :contentReference[oaicite:26]{index=26}

        if not custom_tag_id:
            return JsonResponse({"success": False, "error": "Custom tag is required!"})

        if not uploaded_files:
            return JsonResponse({"success": False, "error": "No files uploaded!"})

        try:
            # Validate UHID once
            uhid_int = int(uhid)
            if uhid_int > 2147483647 or uhid_int < -2147483648:
                raise ValidationError("UHID is too large or invalid!")
        except ValueError:
            return JsonResponse({"success": False, "error": "UHID must be a valid number!"})
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e)})

        # Validate custom tag
        try:
            tag_obj = CustomTag.objects.get(id=custom_tag_id, is_deleted=False)
        except CustomTag.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid custom tag selected."})

        # Process each PDF file individually
        results = []
        for pdf in uploaded_files:
            file_name = pdf.name
            file_size = pdf.size
            file_type = pdf.content_type

            print(f"Received UHID (from GET): {uhid}")
            print(f"Received File: {file_name}")
            print(f"Received Custom Tag: {custom_tag_id}")
            print(f"File Size: {file_size} bytes")
            print(f"File Type: {file_type}")

            try:
                # Validate size
                if file_size > MAX_FILE_SIZE:
                    raise ValidationError(f"\"{file_name}\" exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit!")

                # Validate MIME type is PDF
                if file_type != "application/pdf":
                    raise ValidationError(f"\"{file_name}\" unsupported type! Only PDF files are allowed.")

                # Save this PDF to the UploadedFile model
                UploadedFile.objects.create(
                    user=request.user,
                    patient=patient,
                    file_path=pdf,  # Django will handle storing the PDF
                    custom_tag=tag_obj,
                    file_size=file_size,
                    file_type=file_type
                )

                print(f"✅ \"{file_name}\" uploaded successfully.")
                results.append({"file": file_name, "success": True})

            except ValidationError as e:
                print(f"❌ Validation error for {file_name}: {e}")
                results.append({"file": file_name, "success": False, "error": str(e)})
                # Continue to attempt saving other files

            except Exception:
                # Log the traceback for debugging
                print("❌ ERROR OCCURRED:", traceback.format_exc())
                results.append({"file": file_name, "success": False, "error": "Unexpected server error"})

        # Determine overall success only if every PDF succeeded
        all_success = all(r.get("success") for r in results)
        return JsonResponse({"success": all_success, "results": results})

    # GET: render the upload page
    return render(request, "echs/upload_file_pdf2pdf.html", {
        "uhid": uhid,
        "patient_name": patient_name,
        "custom_tags": custom_tags
    })



@login_required
def view_images_home(request, uhid):
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        return render(request, "echs/view_images.html", {
            "uhid": uhid,
            "images": [],
            "patient_name": "None"
        })
        
    patient_name = patient.patient_name

    # Fetch and optimize related fields
    captured_images = CapturedImage.objects.filter(patient__uhid=uhid, is_deleted=False).select_related(
        'user__designation', 'user__department', 'patient'
    ).order_by('-timestamp')

    uploaded_images = UploadedImage.objects.filter(patient__uhid=uhid, is_deleted=False).select_related(
        'user__designation', 'user__department', 'patient'
    ).order_by('-timestamp')

        
    # Add metadata and tag image type
    for image in captured_images:
        image.source_type = 'captured'

    for image in uploaded_images:
        image.source_type = 'uploaded'

    # Merge and sort
    all_images = sorted(
        chain(captured_images, uploaded_images),
        key=attrgetter('timestamp'),
        reverse=True
    )

    for image in all_images:
        # Calculate size in KB and MB
        try:
            if image.image_size:
                size = int(image.image_size)
                image.image_size_kb = round(size / 1024, 2)
                image.image_size_mb = round(image.image_size_kb / 1024, 2)
            else:
                image.image_size_kb = None
                image.image_size_mb = None
        except Exception as e:
            image.image_size_kb = None
            image.image_size_mb = None
            print(f"[ERROR] Invalid image size for image ID {image.id}: {e}")

        # Extract filename
        image.filename = os.path.basename(image.image_path.name)

        # Add location info for captured images
        if isinstance(image, CapturedImage):
            image.location = f"{image.latitude}, {image.longitude}" if image.latitude and image.longitude else "Unknown Location"
        else:
            image.location = "Uploaded (no location)"

        # Full name
        image.user_full_name = getattr(image.user, 'full_name', None) or "Unknown User"

        # Designation and Department (safe fallback)
        image.user_designation = getattr(image.user.designation, 'title', None)
        image.user_designation_other = getattr(image.user, 'designation_other', None)
        image.user_department = getattr(image.user.department, 'name', None)
        image.user_department_other = getattr(image.user, 'department_other', None)

        # 🔍 Debug Logging
        print("=" * 50)
        print(f"Image ID: {image.id} | Source: {image.source_type.upper()}")
        print(f"User: {image.user_full_name}")
        print(f"Designation: {image.user_designation or ''} ({image.user_designation_other or ''})")
        print(f"Department: {image.user_department or ''} ({image.user_department_other or ''})")
        print(f"Location: {image.location}")
        print(f"Size: {image.image_size_kb} KB | {image.image_size_mb} MB")
        print(f"Filename: {image.filename}")
        print("=" * 50)

    return render(request, 'echs/view_images.html', {
        'uhid': uhid,
        'images': all_images,
        'patient_name': patient_name
    })



@login_required
def download_all_images(request, uhid):
    """
    Creates a ZIP file with all images (captured + uploaded) for the given UHID and returns it.
    """
    patient = get_object_or_404(EchsPatientMaster, uhid=uhid)

    captured_images = CapturedImage.objects.filter(patient=patient, is_deleted=False)
    uploaded_images = UploadedImage.objects.filter(patient=patient, is_deleted=False)


    # Merge and sort by timestamp descending
    all_images = sorted(
        chain(captured_images, uploaded_images),
        key=attrgetter('timestamp'),
        reverse=True
    )

    # Prepare ZIP response
    zip_filename = f"UHID_{uhid}_images.zip"
    response = HttpResponse(content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'

    with zipfile.ZipFile(response, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for image in all_images:
            if image.image_path:  # Ensure path exists
                try:
                    file_path = image.image_path.path  # Absolute path
                    filename = os.path.basename(file_path) # Original filename

                    # Write the file to the ZIP archive with its original name
                    zip_file.write(file_path, arcname=filename)
                except Exception as e:
                    print(f"[ERROR] Could not add image ID {image.id} to ZIP: {e}")

    return response



@login_required
def delete_image(request, model, id):

    # --------------------------
    # Identify Image Model
    # --------------------------
    if model == "captured":
        obj_model = CapturedImage
    elif model == "uploaded":
        obj_model = UploadedImage
    else:
        messages.error(request, "Invalid model type.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # --------------------------
    # Get Image Object
    # --------------------------
    image = get_object_or_404(obj_model, id=id)

    if image.is_deleted:
        messages.warning(request, "Image already deleted.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    patient = image.patient

    # --------------------------
    # Find linked PDF using GenericForeignKey
    # --------------------------
    content_type = ContentType.objects.get_for_model(obj_model)

    linked_pdfs = OtherUploadedFile.objects.filter(
        content_type=content_type,
        object_id=image.id,
        is_deleted=False
    )

    # --------------------------
    # Move & Soft delete linked PDFs
    # --------------------------
    for pdf in linked_pdfs:

        # if pdf.file_path and os.path.exists(pdf.file_path.path):

            # old_pdf_path = pdf.file_path.path

            # deleted_pdf_folder = os.path.join(
            #     settings.MEDIA_ROOT,
            #     f"UHID_{patient.uhid}",
            #     f"UHID_{patient.uhid}_deleted_files"
            # )

            # os.makedirs(deleted_pdf_folder, exist_ok=True)

            # new_pdf_path = os.path.join(
            #     deleted_pdf_folder,
            #     os.path.basename(old_pdf_path)
            # )

            # shutil.move(old_pdf_path, new_pdf_path)

            # rel_path_pdf = os.path.relpath(new_pdf_path, settings.MEDIA_ROOT)
            # pdf.file_path.name = rel_path_pdf.replace("\\", "/")

        pdf.is_deleted = True
        pdf.deleted_on = timezone.now()
        pdf.deleted_by = request.user
        pdf.save()

    # --------------------------
    # Move Image physical file
    # --------------------------
    # if image.image_path and os.path.exists(image.image_path.path):

        # old_path = image.image_path.path

        # deleted_image_folder = os.path.join(
        #     settings.MEDIA_ROOT,
        #     f"UHID_{patient.uhid}",
        #     f"UHID_{patient.uhid}_deleted_files"
        # )

        # os.makedirs(deleted_image_folder, exist_ok=True)

        # new_path = os.path.join(
        #     deleted_image_folder,
        #     os.path.basename(old_path)
        # )

        # shutil.move(old_path, new_path)

        # relative_path = os.path.relpath(new_path, settings.MEDIA_ROOT)
        # image.image_path.name = relative_path.replace("\\", "/")

    # --------------------------
    # Soft delete Image instance
    # --------------------------
    image.is_deleted = True
    image.deleted_on = timezone.now()
    image.deleted_by = request.user
    image.save()

    messages.success(request, "Image and linked PDF deleted successfully.")
    # return redirect(request.META.get("HTTP_REFERER", "/"))
    return redirect(f"{reverse('echs:view_images_home', kwargs={'uhid': patient.uhid})}?deleted=1")



@login_required
def view_files_home_uhid(request, uhid):
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        return render(request, 'echs/view_files.html', {
            'files': [],
            'patient_name': None,
            'uhid': uhid,
        })

    # Fetch files via patient FK
    patient_name = patient.patient_name
    files = UploadedFile.objects.filter(patient=patient,is_deleted=False).order_by('-timestamp')

    for file in files:
        # Calculate sizes
        file.file_size_kb = round(file.file_path.size / 1024, 2)  # Convert to KB
        file.file_size_mb = round(file.file_path.size / (1024 * 1024), 2)  # Convert to MB

        # Convert timestamp to local timezone and format nicely: "12-May-2025 10:15 AM"
        local_timestamp = timezone.localtime(file.timestamp)
        file.formatted_datetime = local_timestamp.strftime('%d-%b-%Y %I:%M %p')

        # Debugging outputs
        print(f"📝 Filename: {file.filename}")
        print(f"🌐 File URL: {file.file_path.url}")
        print(f"📂 File Path: {file.file_path.path}")
        
        # Check if file actually exists on disk
        if os.path.exists(file.file_path.path):
            print(f"✅ File exists: {file.file_path.path}")
        else:
            print(f"❌ Missing file: {file.file_path.path}")

    return render(request, 'echs/view_files.html', {
        'files': files,
        "patient_name":patient_name,
        'uhid': uhid
    })



@login_required
def download_all_files(request, uhid):
    """Creates a ZIP file with all uploaded files for the given UHID and returns it."""
     # 1️⃣ Get patient from UHID
    patient = get_object_or_404(EchsPatientMaster, uhid=uhid)

    # 2️⃣ Fetch uploaded files using patient FK
    files = UploadedFile.objects.filter(patient=patient, is_deleted=False)

    # files = get_list_or_404(UploadedFile, uhid=uhid)  # Get all files for UHID

    zip_filename = f"UHID_{uhid}_files.zip"
    response = HttpResponse(content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'

    with zipfile.ZipFile(response, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if file.file_path:  # Ensure file exists
                file_path = file.file_path.path  # Absolute file path
                filename = os.path.basename(file_path)  # Retain original filename
                
                zip_file.write(file_path, filename)

    return response


@login_required
def delete_uploaded_pdf(request, id):
    file = get_object_or_404(UploadedFile, id=id)

    # ❌ Prevent double delete
    if file.is_deleted:
        messages.warning(request, "PDF file already deleted.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # -----------------------------
    # FILE MOVE LOGIC
    # -----------------------------
    # if file.file_path and os.path.exists(file.file_path.path):
    #     old_path = file.file_path.path

    #     # New deleted folder
    #     deleted_folder = os.path.join(
    #         settings.MEDIA_ROOT,
    #         f"UHID_{file.patient.uhid}",
    #         f"UHID_{file.patient.uhid}_deleted_files"
    #     )

    #     os.makedirs(deleted_folder, exist_ok=True)

    #     new_path = os.path.join(
    #         deleted_folder,
    #         os.path.basename(old_path)
    #     )

    #     shutil.move(old_path, new_path)

    #     # Convert OS path → relative path → URL format
    #     relative_path = os.path.relpath(new_path, settings.MEDIA_ROOT)
    #     relative_path = relative_path.replace("\\", "/")   # <<< FIX HERE

    #     file.file_path.name = relative_path



    # -----------------------------
    # SOFT DELETE FIELDS
    # -----------------------------
    file.is_deleted = True
    file.deleted_on = timezone.now()
    file.deleted_by = request.user
    file.save()

    messages.success(request, "PDF file deleted successfully.")
    # return redirect(request.META.get("HTTP_REFERER", "/"))
    return redirect(f"{reverse('echs:view_files_home', kwargs={'uhid': file.patient.uhid})}?deleted=1")



@login_required
def view_other_files(request, uhid):
    patient = EchsPatientMaster.objects.filter(uhid=uhid).first()

    if not patient:
        return render(request, 'echs/view_files.html', {
            'files': [],
            'patient_name': None,
            'uhid': uhid,
        })

    # Fetch files via patient FK
    patient_name = patient.patient_name
    files = OtherUploadedFile.objects.filter(patient=patient, is_deleted=False).order_by('-timestamp')

    for file in files:
        # Calculate sizes
        file.file_size_kb = round(file.file_path.size / 1024, 2)  # Convert to KB
        file.file_size_mb = round(file.file_path.size / (1024 * 1024), 2)  # Convert to MB

        # Convert timestamp to local timezone and format nicely: "12-May-2025 10:15 AM"
        local_timestamp = timezone.localtime(file.timestamp)
        file.formatted_datetime = local_timestamp.strftime('%d-%b-%Y %I:%M %p')

        # Debugging outputs
        print(f"📝 Filename: {file.filename}")
        print(f"🌐 File URL: {file.file_path.url}")
        print(f"📂 File Path: {file.file_path.path}")
        
        # Check if file actually exists on disk
        if os.path.exists(file.file_path.path):
            print(f"✅ File exists: {file.file_path.path}")
        else:
            print(f"❌ Missing file: {file.file_path.path}")

    return render(request, 'echs/view_other_files.html', {
        'files': files,
        "patient_name":patient_name,
        'uhid': uhid
    })



@login_required
def download_all_other_files(request, uhid):
    patient = get_object_or_404(EchsPatientMaster, uhid=uhid)

    files = OtherUploadedFile.objects.filter(patient=patient, is_deleted=False)

    zip_filename = f"UHID_{uhid}_files.zip"
    response = HttpResponse(content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'

    with zipfile.ZipFile(response, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if file.file_path:  # Ensure file exists
                file_path = file.file_path.path  # Absolute file path
                filename = os.path.basename(file_path)  # Retain original filename
                
                zip_file.write(file_path, filename)

    return response



@login_required
def view_deleted_items(request, uhid):
    patient = EchsPatientMaster.objects.filter(uhid=uhid, ).first()

    if not patient:
        return render(request, 'echs/view_deleted_items.html', {
            'files': [],
            'patient_name': None,
            'uhid': uhid,
        })

    # Fetch files via patient FK
    patient_name = patient.patient_name

    # Deleted captured images
    captured = CapturedImage.objects.filter(patient=patient, is_deleted=True, deleted_by_id = request.user.id).annotate(source_type=Value("captured", output_field=CharField()))

    # Deleted uploaded images
    uploaded = UploadedImage.objects.filter(patient=patient, is_deleted=True, deleted_by_id = request.user.id).annotate(source_type=Value("uploaded", output_field=CharField()))

    # Deleted pdf files
    pdf_files = UploadedFile.objects.filter(patient=patient, is_deleted=True, deleted_by_id = request.user.id).annotate(source_type=Value("pdf", output_field=CharField()))

    # Merge all deleted items
    items  = list(chain(captured, uploaded, pdf_files))

    files = []


    for f in items:

        # ----------------
        # File path logic
        # ----------------
        if f.source_type == "pdf":
            file_type = "PDF"
            path = f.file_path.path if f.file_path else None
            url = f.file_path.url if f.file_path else None
        else:
            file_type = "Image"
            path = f.image_path.path if f.image_path else None
            url = f.image_path.url if f.image_path else None

        # ----------------
        # filename
        # ----------------
        filename = os.path.basename(path) if path else "Unknown"

        # ----------------
        # formatted date
        # ----------------
        ts = timezone.localtime(f.timestamp)
        formatted_datetime = ts.strftime("%d-%b-%Y %I:%M %p")

        # ----------------
        # file size
        # ----------------
        size_kb = None
        size_mb = None

        if path and os.path.exists(path):
            file_size = os.path.getsize(path)
            size_kb = round(file_size / 1024, 2)
            size_mb = round(file_size / (1024 * 1024), 2)


        # ----------------
        # append final dict
        # ----------------
        files.append({
            "id": f.id,
            "filename": filename,
            "formatted_datetime": formatted_datetime,
            "file_size_kb": size_kb,
            "file_size_mb": size_mb,
            "file_type": file_type,
            "source": f.source_type,
            "file_url": url,
            "user": f.user,
            "user_id": f.user_id,
            "deleted_by": f.deleted_by_id,
            "custom_tag": getattr(f, "custom_tag", None),
            "designation": getattr(f.user, "designation", None),
            "designation_other": getattr(f.user, "designation_other", None),
            "department": getattr(f.user, "department", None),
            "department_other": getattr(f.user, "department_other", None),
        })

    # sort by timestamp desc
    files.sort(key=lambda x: x["formatted_datetime"], reverse=True)

    return render(request, "echs/view_deleted_items.html", {
        "files": files,
        "patient_name": patient_name,
        "uhid": uhid,
    })



@login_required
def restore_item(request, file_id, source):

    model = None

    if source == "captured":
        model = CapturedImage
    elif source == "uploaded":
        model = UploadedImage
    elif source == "pdf":
        model = UploadedFile
    else:
        messages.error(request, "Invalid source")
        return redirect("echs:view_deleted_items", uhid=request.GET.get("uhid"))

    obj = get_object_or_404(model, id=file_id)

    obj.is_deleted = False
    obj.deleted_by = None
    obj.deleted_on = None
    obj.save()

    # restore_physical_file(obj)

    tag_obj = getattr(obj, "custom_tag", None)

    if tag_obj and tag_obj.id in [10, 11]:
        content_type = ContentType.objects.get_for_model(obj)
        other = OtherUploadedFile.objects.filter(
            patient=obj.patient,
            content_type=content_type,
            object_id=obj.id,
            is_deleted=True
        ).first()

        if other:
            # restore_physical_file(other)

            other.is_deleted = False
            other.deleted_on = None
            other.deleted_by = None
            other.save()
        
    
    messages.success(request, "File restored successfully")
    return redirect(f"{reverse('echs:view_deleted_items', kwargs={'uhid': obj.patient.uhid})}?restored=1")



def restore_physical_file(obj):
   
    deleted_folder = os.path.join(
        settings.MEDIA_ROOT,
        f"UHID_{obj.patient.uhid}",
        f"UHID_{obj.patient.uhid}_deleted_files"
    )

    file_field = None
    field_name = None
    if hasattr(obj, "image_path") and obj.image_path:
        file_field = obj.image_path
        field_name = "image_path"
    elif hasattr(obj, "file_path") and obj.file_path:
        file_field = obj.file_path
        field_name = "file_path"

    if not file_field:
        return False

    filename = os.path.basename(file_field.name)
    deleted_path = os.path.join(deleted_folder, filename)

    if not os.path.exists(deleted_path):
        return False

    original_folder = os.path.join(settings.MEDIA_ROOT, obj.folder_path)
    os.makedirs(original_folder, exist_ok=True)
    new_path = os.path.join(original_folder, filename)

    try:
        shutil.copy2(deleted_path, new_path)
        time.sleep(0.2) 
        os.remove(deleted_path)
    except PermissionError:
        return False

    rel_path = os.path.relpath(new_path, settings.MEDIA_ROOT).replace("\\", "/")
    setattr(obj, field_name, rel_path)
    obj.save(update_fields=[field_name])

    return True






