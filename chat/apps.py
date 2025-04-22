from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    verbose_name = _('Live Chat')
    
    def ready(self):
        # Add admin site link
        from django.contrib.admin import AdminSite
        
        # Store the original method
        original_get_app_list = AdminSite.get_app_list
        
        # Define the new method with the correct signature
        def get_app_list(self, request, app_label=None):
            """
            Return a sorted list of all the installed apps that have been
            registered in this site.
            """
            if app_label:
                # Call the original method
                app_list = original_get_app_list(self, request, app_label)
                return app_list
            
            # Get the original app list
            app_list = original_get_app_list(self, request)
            
            # Add custom link
            app_list.append({
                'name': 'Live Chat',
                'app_label': 'chat',
                'models': [{
                    'name': 'Chat Dashboard',
                    'object_name': 'chat_dashboard',
                    'admin_url': '/chat/staff/',
                    'view_only': True,
                }],
            })
            
            return app_list
        
        # Replace the original method
        AdminSite.get_app_list = get_app_list
