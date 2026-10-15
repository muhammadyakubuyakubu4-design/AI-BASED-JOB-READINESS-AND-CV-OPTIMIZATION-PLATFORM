import zipfile
from django import forms
from .models import CVUpload
from django.conf import settings


class CVUploadForm(forms.ModelForm):
    """Form for uploading a CV file."""

    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx',
        }),
        help_text='Upload your CV in PDF or DOCX format (max 5MB)'
    )

    class Meta:
        model = CVUpload
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Please select a file to upload.')

        # Check file extension
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in settings.ALLOWED_CV_EXTENSIONS:
            raise forms.ValidationError(
                f'Invalid file type. Only {", ".join(settings.ALLOWED_CV_EXTENSIONS).upper()} files are allowed.'
            )

        # Check file size
        if file.size > settings.MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                f'File too large. Maximum size is {settings.MAX_CV_FILE_SIZE_MB}MB.'
            )

        # Content-based validation — verify file header bytes match extension
        header = file.read(2048)
        file.seek(0)
        if ext == 'pdf' and not header.startswith(b'%PDF-'):
            raise forms.ValidationError('File does not appear to be a valid PDF.')
        elif ext == 'docx':
            if not header.startswith(b'PK\x03\x04'):
                raise forms.ValidationError('File does not appear to be a valid DOCX.')

        return file
