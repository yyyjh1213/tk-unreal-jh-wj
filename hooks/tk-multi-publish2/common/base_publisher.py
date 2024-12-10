"""
Base publisher class for publish hooks.
"""
import sgtk
from . import utils

HookBaseClass = sgtk.get_hook_baseclass()

class BasePublisher(HookBaseClass):
    """
    Base class for publishers with common functionality.
    """
    
    @property
    def settings(self):
        """
        Dictionary defining the settings that this publisher expects to receive.
        """
        return {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published files. Should correspond to a template defined in templates.yml."
            },
        }
    
    @property
    def publish_file_type(self):
        """
        The type of file being published. Must be implemented by subclasses.
        """
        raise NotImplementedError
    
    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        """
        accepted_types = self.accepted_item_types
        
        if item.type in accepted_types:
            return {
                "accepted": True,
                "enabled": True,
                "checked": True
            }
            
        return {
            "accepted": False,
            "enabled": False,
            "checked": False
        }
    
    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        return True
    
    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        # Get the publish template
        template = utils.get_template_from_settings(settings, self.parent)
        
        # Get the publish path
        publish_path = self._get_publish_path(template, item)
        
        # Ensure the publish folder exists
        utils.ensure_folder_exists(publish_path)
        
        # Do the actual publish
        if not self._do_publish(settings, item, publish_path):
            return False
        
        # Register the publish
        publish_data = utils.get_publish_data(
            self.parent, 
            item, 
            publish_path, 
            self.publish_file_type
        )
        self._register_publish(**publish_data)
        
        return True
        
    def _get_publish_path(self, template, item):
        """
        Get the publish path. Override in subclasses if needed.
        """
        return template.apply_fields(item.properties)
        
    def _do_publish(self, settings, item, publish_path):
        """
        Do the actual publish. Must be implemented by subclasses.
        """
        raise NotImplementedError
    
    @property
    def accepted_item_types(self):
        """
        List of item types that this plugin accepts. Must be implemented by subclasses.
        """
        raise NotImplementedError
