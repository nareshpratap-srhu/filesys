app_name = "capture"

from django.urls import path
from . import views

urlpatterns = [
  
    # Root URL For redirecting to Capturing UHIDs
    path('', views.capture_uhid_camera, name='uhid_capture_camera'), 
    # Earlier: path('cap_id_c', views.capture_uhid_camera, name='uhid_capture_camera'), 


    # Processing the logic capture Images & Upload Files 
    path('cap_pic/', views.capture_images, name='image_capture'),  
    path('up_file/', views.upload_file, name='upload_file'), 
    path('up_file_image2pdf/', views.upload_file_image2pdf, name='upload_file_image2pdf'),  
    path('up_file_pdf2pdf/', views.upload_file_pdf2pdf, name='upload_file_pdf2pdf'),  
    path('up_file_image2image/', views.upload_file_image2image, name='upload_file_image2image'), 
    path('up_file_multi_image2image/', views.upload_file_multi_image2image, name='upload_file_multi_image2image'), 


    # Logic for Image & File View
    path('view-images-home/<str:uhid>/', views.view_images_home_uhid, name='view_images_home'),
    path('view-files-home/<str:uhid>/', views.view_files_home_uhid, name='view_files_home'),


    path('download-all-images/<str:uhid>/', views.download_all_images, name='download_all_images'),
    path('download-all-files/<str:uhid>/', views.download_all_files, name='download_all_files'),

    path('uhid_options/', views.uhid_options, name='uhid_options'),

    # ✅ For Uploaded Files Table
    path('uploaded-files-info/', views.uploaded_files_view, name='uploaded_files_info'),
    path('uploaded-images-info/', views.uploaded_images_view, name='uploaded_images_info'),
    path('captured-images-info/', views.captured_images_view, name='captured_images_info'),
    path('all-files-images-info/', views.all_files_images_view, name='all_file_image_info'),

    
    # Excel Export for Uploaded Files
    path('export-uploaded-files/', views.export_uploaded_files_excel, name='export_uploaded_files_excel'),
    path('export-uploaded-images/', views.export_uploaded_images_excel, name='export_uploaded_images_excel'),
    path('export-captured-images/', views.export_captured_images_excel, name='export_captured_images_excel'),
    path('export-all-files-images/', views.export_all_files_excel, name='export_all_files_images_excel'),

    # Add this new path for the issue reporting form:
    path('report-issue/', views.report_issue, name='report_issue'),
    path("manage-issues/", views.manage_issues, name="manage_issues"),

    # Delete Logic
    path('delete-image/<str:model>/<str:id>/', views.delete_image, name='delete_image'),
    path('delete-uploaded-pdf/<str:id>/', views.delete_uploaded_pdf, name='delete_uploaded_pdf'),

]
