import os
from django.contrib.contenttypes.models import ContentType
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import logging

from echs.models import OtherUploadedFile

logger = logging.getLogger(__name__)


def generate_pdf_file(patient, captured_image, user):

    if not captured_image or not captured_image.image_path:
        return None

    image_path = captured_image.image_path.path
    if not os.path.exists(image_path):
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 80
    line_gap = 25

    tag_id = None
    tag_obj = None
    tag_name = "NoTag"

    if captured_image.custom_tag:
        tag_obj = captured_image.custom_tag
        tag_id = tag_obj.id
        tag_name = tag_obj.name.replace(" ", "_")

    def draw_label_value(label, value, y_pos):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(80, y_pos, f"{label}:")
        label_width = c.stringWidth(f"{label}:", "Helvetica-Bold", 14)
        c.setFont("Helvetica", 14)
        c.drawString(80 + label_width + 8, y_pos, str(value))

    draw_label_value("HOSPITAL NAME", "HIMALAYAN HOSPITAL", y)
    draw_label_value("PATIENT NAME", patient.patient_name, y - line_gap)

    if tag_id == 10:
        draw_label_value("MOBILE NUMBER", patient.mobile_no, y - (line_gap * 2))
        draw_label_value(
            "DATE OF ADMISSION",
            patient.date_of_admission.strftime('%d-%m-%Y %H:%M hr.'),
            y - (line_gap * 3)
        )

    if tag_id == 11:
        draw_label_value(
            "DATE OF ADMISSION",
            patient.date_of_admission.strftime('%d-%m-%Y %H:%M hr.'),
            y - (line_gap * 2)
        )
        draw_label_value(
            "DATE OF DISCHARGE",
            patient.date_of_discharge.strftime('%d-%m-%Y %H:%M hr.'),
            y - (line_gap * 3)
        )

    try:
        image = ImageReader(image_path)
        c.drawImage(
            image,
            80,
            0,
            width=width - 160,
            height=height + 160,
            preserveAspectRatio=True,
            anchor="c"
        )
    except Exception as e:
        logger.error(f"PDF image draw failed: {e}")

    c.showPage()
    c.save()

    buffer.seek(0)


    # 🔥 Create DB record using upload_to()
    pdf_instance = OtherUploadedFile(
        user=user,
        patient=patient,
        custom_tag=tag_obj,
        content_type=ContentType.objects.get_for_model(captured_image.__class__),
        object_id=captured_image.id
    )

    pdf_instance.file_path.save(
        f"IP_{patient.uhid}_{tag_name}.pdf",
        ContentFile(buffer.read()),
        save=True
    )

    return pdf_instance 
