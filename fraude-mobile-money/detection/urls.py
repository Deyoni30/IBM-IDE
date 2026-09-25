from django.urls import path

from .views import UploadCSVView

urlpatterns = [
    path("upload/", UploadCSVView.as_view(), name="upload-csv"),
]
