from django.urls import path
from core__a.views import *



urlpatterns = [
    path('upload/images/', UploadImagesView.as_view(), name="upload-images"),
]