from django.db import models

class Predictor(models.Model):
    plant_name = models.CharField(max_length=255)
    model_path = models.CharField(max_length=255)
    labels_path = models.CharField(max_length=255)

    def __str__(self):
        return self.plant_name  