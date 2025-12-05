from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_route, name='add_route'),
    path('upload/', views.upload_xml, name='upload_xml'),
    path('routes/', views.routes_list, name='routes_list'),
    path('routes/search/', views.ajax_search, name='ajax_search'),
    path('routes/edit/<int:route_id>/', views.edit_route, name='edit_route'),
    path('routes/delete/<int:route_id>/', views.delete_route, name='delete_route'),
    path('download/', views.download_xml, name='download_xml'),
]