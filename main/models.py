from django.db import models

# Create your models here.
class main (models.Model):
    title = models.CharField(max_length=30)
    content = models.TextField()