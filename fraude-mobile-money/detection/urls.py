from django.urls import path

from .views import AlerteListView, UploadCSVView

urlpatterns = [
    path("upload/", UploadCSVView.as_view(), name="upload-csv"),
    path("alertes/", AlerteListView.as_view(), name="alerte-list"),
]
