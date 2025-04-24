from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Sélectionnez un fichier WordPress XML")