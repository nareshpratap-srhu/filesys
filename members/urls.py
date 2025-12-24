app_name = "members"

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # User registration
    path('register/', views.register, name='register'),

    # User login
    path('login/', views.login_view, name='login'),

    # User Approval, Reset Password, Configurations by Superuser
    path('user-approval/', views.user_approval, name='user_approval'),
    path('configs/', views.configs, name='configs'),
    
    #select service type
    path('service-choice/', views.service_choice, name='service_choice'),

    # User List Excel Export
    path('export-user-list-excel/', views.export_user_list_excel, name='export_user_list_excel'),
    path('export-department-list-excel/', views.export_department_list_excel, name='export_department_list_excel'),
    path('export-ward-list-excel/', views.export_ward_list_excel, name='export_ward_list_excel'),
    path('export-designation-list-excel/', views.export_designation_list_excel, name='export_designation_list_excel'),
    path('export-tag-list-excel/', views.export_tag_list_excel, name='export_tag_list_excel'),

    # Download and Upload User Template    
    path('download-user-template/', views.download_user_template, name='download_user_template'),
    path('upload-user-template/', views.upload_user_template, name='upload_user_template'),

    #Reset password by Superuser
    path('reset-pass/', views.reset_password_bysuper, name='reset_password_bysuper'),

    #Unblock User by Superuser
    path('unblock-user/', views.unblock_user_bysuper, name='unblock_user_bysuper'),

    # Tag Master
    path('manage-custom-tags/', views.manage_custom_tags, name='manage_custom_tags'),
    path('delete/<int:pk>/', views.delete_custom_tag, name='delete_custom_tag'),
    path('restore/<int:pk>/', views.restore_custom_tag, name='restore_custom_tag'),

    #Department Master
    path('departments/', views.manage_departments, name='manage_departments'),
    path('departments/deactivate/<int:pk>/', views.deactivate_department, name='deactivate_department'),
    path('departments/restore/<int:pk>/', views.restore_department, name='restore_department'),

    # Ward Master
    path('wards/', views.manage_wards, name='manage_wards'),
    path('wards/deactivate/<int:pk>/', views.deactivate_ward, name='deactivate_ward'),
    path('wards/restore/<int:pk>/', views.restore_ward, name='restore_ward'),

    #Designation Master
    path('designations/', views.manage_designations, name='manage_designations'),
    path('designations/deactivate/<int:pk>/', views.deactivate_designation, name='deactivate_designation'),
    path('designations/restore/<int:pk>/', views.restore_designation, name='restore_designation'),


    # User logout
    path('logout/', auth_views.LogoutView.as_view(next_page='members:login'), name='logout'),

    # Profile update page
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),  # New path for profile update
    path('password/update/', views.password_update, name='password_update'),  # New path for password update

    # Password Reset Workflow (Using clean template names 🔥)
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='members/password_reset.html',                   # ✅ ask user for email
            email_template_name='members/password_reset_email.html',        # ✅ email body
            subject_template_name='members/password_reset_subject.txt',     # ✅ email subject
            success_url='/members/password-reset/done/'
        ),
        name='password_reset'
    ),

    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='members/password_reset_done.html'                # ✅ confirmation page
        ),
        name='password_reset_done'
    ),

    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='members/password_reset_confirm.html',            # ✅ set new password
            success_url='/members/reset/done/'
        ),
        name='password_reset_confirm'
    ),

    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='members/password_reset_complete.html'            # ✅ password reset successful
        ),
        name='password_reset_complete'
    ),
]
