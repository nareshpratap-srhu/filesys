from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, CustomTag, Department, Designation, Ward
from django.contrib.auth.forms import PasswordChangeForm

class UserRegisterForm(UserCreationForm):
    # 1️⃣ Full Name field
    full_name = forms.CharField(
        max_length=255,
        required=True,
        label="Full Name",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name',
        'class': 'form-control',
        'style': 'width: 100%;'})
    )

    # 2️⃣ Email field (used as username)
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your valid email',
            'autocomplete': 'username',
            'class': 'form-control',
            'style': 'width: 100%;' 
            }),
        help_text="A valid email address is required."
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=True,
        empty_label="Select Department",
        label="Department",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    department_other = forms.CharField(
        max_length=255,
        required=False,
        label="Specify Department",
        widget=forms.TextInput(attrs={
            'placeholder': 'If Other, specify here',
            'class': 'form-control',
            'style': 'width: 100%;'
        })
    )

    ward = forms.ModelChoiceField(
        queryset=Ward.objects.filter(is_active=True),
        required=False,
        empty_label="Select Ward (optional)",
        label="Ward",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    ward_other = forms.CharField(
        max_length=255,
        required=False,
        label="Specify Ward",
        widget=forms.TextInput(attrs={
            'placeholder': 'If Other, specify here',
            'class': 'form-control',
            'style': 'width: 100%;'
        })
    )

    designation = forms.ModelChoiceField(
        queryset=Designation.objects.filter(is_active=True),
        required=True,
        empty_label="Select Designation",
        label="Designation",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    designation_other = forms.CharField(
        max_length=255,
        required=False,
        label="Specify Designation",
        widget=forms.TextInput(attrs={
            'placeholder': 'If Other, specify here',
            'class': 'form-control',
            'style': 'width: 100%;'
        })
    )

    phone = forms.CharField(
        max_length=15,
        required=True,
        label="Contact",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number',
        'class': 'form-control',
        'style': 'width: 100%;'})
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
    )

    class Meta:
        """Defines the model and fields used in the registration form."""
        model = CustomUser
        fields = [
            'full_name', 'email',
            'department', 'department_other',
            'designation', 'designation_other',
            'ward', 'ward_other',
            'phone', 'password1', 'password2'
        ]
    def clean_email(self):
        """3️⃣ Ensure email is unique and stored in lowercase (case-insensitive)."""
        email = self.cleaned_data.get("email").lower()  # Normalize email to lowercase
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean(self):
        cleaned = super().clean()

        dept = cleaned.get('department')
        dept_other = cleaned.get('department_other', '').strip()
        if dept and dept.name.lower() in ('other', 'others'):
            if not dept_other:
                self.add_error(
                    'department_other',
                    'Please specify a Department when “Other” is selected.'
                )
            # else: dept_other is non-empty → keep it (no clearing)
        else:
            # Dept isn’t “Other” → clear any stale text
            cleaned['department_other'] = ''

        # Same pattern for designation
        desig = cleaned.get('designation')
        desig_other = cleaned.get('designation_other', '').strip()
        if desig and desig.title.lower() in ('other', 'others'):
            if not desig_other:
                self.add_error(
                    'designation_other',
                    'Please specify a Designation when “Other” is selected.'
                )
        else:
            cleaned['designation_other'] = ''

        # Ward “Other” handling
        ward = cleaned.get('ward')
        ward_other = cleaned.get('ward_other', '').strip()
        if ward and ward.ward_name.lower() in ('other', 'others'):
            if not ward_other:
                self.add_error(
                    'ward_other',
                    'Please specify a Ward when “Other” is selected.'
                )
        else:
            # if not “Other”, clear any leftover text
            cleaned['ward_other'] = ''

        return cleaned   


    def save(self, commit=True):
        user = super().save(commit=False)
        print(">> In save(), department_other:", self.cleaned_data.get('department_other'))

        # Always assign the FK, even if “Other”
        # Then persist the free-text separately
        if user.department and user.department.name.lower() in ('other', 'others'):
            user.department_other = self.cleaned_data.get('department_other', '').strip()
        else:
            user.department_other = ''

        if user.designation and user.designation.title.lower() in ('other', 'others'):
            user.designation_other = self.cleaned_data.get('designation_other', '').strip()
        else:
            user.designation_other = ''

        # Ward: if “Other” selected, save ward_other; else clear
        if user.ward and user.ward.ward_name.lower() in ('other', 'others'):
            user.ward_other = self.cleaned_data.get('ward_other', '').strip()
        else:
            user.ward_other = ''

        if commit:
            user.save()
        return user
    
class UserLoginForm(AuthenticationForm):
    
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
    )
    
    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()  # Normalize to lowercase

class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    employee_id = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Employee ID'
        })
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': '-- Select Department --',
            'data-allow-clear': 'true'
        }),
        empty_label="-- Select Department --"
    )
    department_other = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify Department'
        })
    )

    ward = forms.ModelChoiceField(
        queryset=Ward.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': '-- Select ward (optional) --',
            'data-allow-clear': 'true'
        }),
        empty_label="Select Ward"
    )
    ward_other = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify Ward'
        })
    )
    
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': '-- Select Department --',
            'data-allow-clear': 'true'
        }),
        empty_label="-- Select Designation --"
    )
    designation_other = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify Designation'
        })
    )

    phone = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone'
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'email', 'employee_id',
            'department', 'department_other',
            'ward', 'ward_other',
            'designation', 'designation_other',
            'phone'
        ]

    def clean(self):
        cleaned = super().clean()

        # Department “Other” handling
        dept = cleaned.get('department')
        dept_other = cleaned.get('department_other', '').strip()
        if dept and dept.name.lower() in ('other', 'others'):
            if not dept_other:
                self.add_error(
                    'department_other',
                    'Please specify a Department when “Other” is selected.'
                )
            # else: user entered text → keep it
        else:
            # not “Other” → clear any leftover text
            cleaned['department_other'] = ''
        
        # Ward “Other” handling
        ward = cleaned.get('ward')
        ward_other = cleaned.get('ward_other', '').strip()
        if ward and ward.ward_name.lower() in ('other', 'others'):
            if not ward_other:
                self.add_error(
                    'ward_other',
                    'Please specify a Ward when “Other” is selected.'
                )
        else:
            cleaned['ward_other'] = ''
        
        # Designation “Other” handling
        desig = cleaned.get('designation')
        desig_other = cleaned.get('designation_other', '').strip()
        if desig and desig.title.lower() in ('other', 'others'):
            if not desig_other:
                self.add_error(
                    'designation_other',
                    'Please specify a Designation when “Other” is selected.'
                )
        else:
            cleaned['designation_other'] = ''

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)

        # If the user picked “Other” (or “Others”), store their custom text;
        # otherwise clear out any stale department_other.
        if user.department and user.department.name.lower() in ('other', 'others'):
            user.department_other = self.cleaned_data.get('department_other', '').strip()
        else:
            user.department_other = ''

        # Same for Ward
        if user.ward and user.ward.ward_name.lower() in ('other', 'others'):
            user.ward_other = self.cleaned_data.get('ward_other', '').strip()
        else:
            user.ward_other = ''

        # Same for designation
        if user.designation and user.designation.title.lower() in ('other', 'others'):
            user.designation_other = self.cleaned_data.get('designation_other', '').strip()
        else:
            user.designation_other = ''

        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Form for changing the user's password.
    This is a subclass of Django's built-in PasswordChangeForm.
    """
    class Meta:
        model = CustomUser
        fields = ['old_password', 'new_password1', 'new_password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally, you can modify widget attributes to add placeholder text or style
        self.fields['old_password'].widget.attrs.update({'placeholder': 'Current Password'})
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'New Password'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'Confirm New Password'})


class CustomTagForm(forms.ModelForm):
    class Meta:
        model = CustomTag
        fields = ['name', 'abbreviation', 'type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter custom tag'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter abbreviation'}),
            'type': forms.Select(attrs={'class': 'form-control'})
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'abbreviation']
        widgets = {
            'name': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter department name'
            }),
            'abbreviation': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter abbreviation'
            }),
        }

class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ['ward_name', 'ward_abbre']
        widgets = {
            'ward_name': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter ward name'
            }),
            'ward_abbre': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter abbreviation'
            }),
        }

class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['title', 'abbreviation']
        widgets = {
            'title': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter designation title'
            }),
            'abbreviation': forms.TextInput({
                'class': 'form-control',
                'placeholder': 'Enter abbreviation'
            }),
        }


class UploadExcelForm(forms.Form):
    file = forms.FileField(
        label='Select Excel (.xlsx) file',
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'})
    )


