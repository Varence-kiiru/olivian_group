from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('category/<slug:slug>/', views.category_projects, name='category_projects'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('<slug:slug>/', views.project_detail, name='project_detail'),
]
