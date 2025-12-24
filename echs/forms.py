from django import forms
from .models import IssueReport

# class IssueReportForm(forms.ModelForm):
#     description = forms.CharField(
#         widget=forms.Textarea(attrs={
#             'rows': 2,
#             'placeholder': 'Type here...',
#             'class': 'form-control',  # add Bootstrap class here
#             'style': 'resize:none; font-size: 0.8rem;'  # optional: disable resizing if you want
#         }),
#         required=True
#     )
#     attachment = forms.FileField(
#         required=False,
#         label="Attach a file (PDF or Image)",
#         widget=forms.ClearableFileInput(attrs={
#             'class': 'form-control'  # add Bootstrap class here too
#         })
#     )

#     class Meta:
#         model = IssueReport
#         fields = ['description', 'attachment']

#     def clean_description(self):
#         description = self.cleaned_data.get('description', '')
#         word_list = description.strip().split()
#         word_count = len(word_list)
#         if word_count > 40:
#             raise forms.ValidationError(f"Description cannot exceed 40 words (you typed {word_count}).")

#         return description

#     def clean_attachment(self):
#         attachment = self.cleaned_data.get('attachment')
#         if attachment:
#             valid_extensions = ['pdf', 'jpg', 'jpeg', 'png']
#             ext = attachment.name.split('.')[-1].lower()
#             if ext not in valid_extensions:
#                 raise forms.ValidationError("Unsupported file extension. Allowed: pdf, jpg, jpeg, png.")
#             if attachment.size > 10 * 1024 * 1024:  # 10MB limit
#                 raise forms.ValidationError("File size must be under 10MB.")
#         return attachment
    
# class IssueAdminUpdateForm(forms.ModelForm):
#     class Meta:
#         model = IssueReport
#         fields = ['current_status', 'admin_remark']
#         widgets = {
#             'current_status': forms.Select(attrs={
#                 'class': 'form-select form-select-sm'
#             }),
#             'admin_remark': forms.Textarea(attrs={
#                 'class': 'form-control form-control-sm',
#                 'rows': 3,
#                 'placeholder': 'Remarks, if any'
#             }),
#         }


    

