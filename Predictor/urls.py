
from django.urls import path,include
from . import views
urlpatterns = [
    path("<int:plant_id>/", views.predict_disease),
]