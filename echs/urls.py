app_name = "echs"

from django.urls import path
from . import views

urlpatterns = [

    path('uhid_capture_camera', views.capture_uhid_camera, name='uhid_capture_camera'),
    path('echs_uhid_options/', views.echs_uhid_options, name='echs_uhid_options'),
    
    path("register_patient/", views.register_patient, name="register_patient"),
    path('check-discharge-status/',views.check_discharge_status,name='check_discharge_status'),

    path('image_capture/', views.echs_image_capture, name='echs_image_capture'),
    path('up_file_image2image/', views.upload_file_image2image, name='upload_file_image2image'),
    path('up_file_multi_image2image/', views.upload_file_multi_image2image, name='upload_file_multi_image2image'),
    path('up_file_image2pdf/', views.upload_file_image2pdf, name='upload_file_image2pdf'),
    path('up_file_pdf2pdf/', views.upload_file_pdf2pdf, name='upload_file_pdf2pdf'), 
 

    path('view-images-home/<str:uhid>/', views.view_images_home, name='view_images_home'),
    path('download-all-images/<str:uhid>/', views.download_all_images, name='download_all_images'),
    path('delete-image/<str:model>/<str:id>/', views.delete_image, name='delete_image'),

    path('view-files-home/<str:uhid>/', views.view_files_home_uhid, name='view_files_home'),
    path('download-all-files/<str:uhid>/', views.download_all_files, name='download_all_files'),
    path('delete-uploaded-pdf/<str:id>/', views.delete_uploaded_pdf, name='delete_uploaded_pdf'),

    path('view-other-files/<str:uhid>/', views.view_other_files, name='view_other_files'),
    path('download-all-other-files/<str:uhid>/', views.download_all_other_files, name='download_all_other_files'),
    # path('delete-other-files/<str:id>/', views.delete_other_files, name='delete_other_files'),

    path('view-deleted-items/<str:uhid>/', views.view_deleted_items, name='view_deleted_items'),
    path("restore-item/<int:file_id>/<str:source>/", views.restore_item, name="restore_item"),

   
]
