from django.urls import path
from . import views

app_name = 'refactai_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_zip, name='upload_zip'),
    path('results/', views.compare_sessions, name='compare_sessions'),
    path('results/<uuid:session_id>/', views.results, name='results'),
    path('status/<uuid:session_id>/', views.check_status, name='check_status'),
    path('download/<uuid:session_id>/', views.download_refactored, name='download_refactored'),
    path('file/<uuid:session_id>/<int:file_id>/', views.view_file, name='view_file'),
    path('health/', views.health_check, name='health_check'),
    path('docs/', views.documentation, name='documentation'),
    path('docs/setup-guide/', views.setup_guide, name='setup_guide'),
    path('docs/new-user-setup/', views.new_user_setup, name='new_user_setup'),
    path('docs/troubleshooting/', views.troubleshooting_guide, name='troubleshooting_guide'),
    path('docs/setup-script/', views.setup_script_info, name='setup_script_info'),
]