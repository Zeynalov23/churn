from django import forms

class CustomerUploadForm(forms.Form):
    file = forms.FileField()
