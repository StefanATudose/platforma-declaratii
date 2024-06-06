from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("menu", views.menu, name  = "menu"),
    path("upload", views.FileFormView.as_view(), name="upload"),
    path("upload_result", views.upload_result, name="upload_result"),
    path("vezideclaratii", views.vezi_declaratii, name="vezideclaratii"),
    path("rezultategenerale", views.rezultate_generale, name="rezultategenerale"),
    path("individ/<int:titular_id>", views.profil_individ, name="individ"),
    path("get_year_data/<int:titular_id>/<int:year>/<int:doc_type>", views.get_year_data, name="get_year_data"),
    path("get_graphs/<int:titular_id>", views.get_graphs, name="get_graphs"),
    path("clasament_search", views.clasament_search, name="clasament_search"),
    path("clasament_results", views.clasament_results, name="clasament_results"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)