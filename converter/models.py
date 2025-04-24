from django.db import models

# Create your models here.
from django.db import models

class WordPressExport(models.Model):
    file = models.FileField(upload_to='wordpress_exports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)