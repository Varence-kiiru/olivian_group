from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('showcase/', views.ProjectShowcaseView.as_view(), name='showcase'),
    path('showcase/<str:project_number>/', views.ProjectShowcaseDetailView.as_view(), name='showcase_detail'),
    # Import showcases - MUST come before project_number patterns
    path('import-showcases/', views.import_showcases_view, name='import_showcases'),
    # API endpoints for AJAX operations
    path('api/<int:project_id>/delete/', views.ProjectDeleteAPIView.as_view(), name='api_delete'),
    path('api/<int:project_id>/complete/', views.ProjectCompleteAPIView.as_view(), name='api_complete'),
    # Project-specific patterns (MUST come last due to <str:project_number> catch-all)
    path('<str:project_number>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<str:project_number>/update/', views.ProjectUpdateView.as_view(), name='update'),
    path('<str:project_number>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
]
