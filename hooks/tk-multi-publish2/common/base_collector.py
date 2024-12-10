"""
Base collector class for publish hooks.
"""
import sgtk
from . import utils

HookBaseClass = sgtk.get_hook_baseclass()

class BaseCollector(HookBaseClass):
    """
    Base class for collectors with common functionality.
    """
    
    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive.
        """
        return {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for work files. Should correspond to a template defined in templates.yml."
            },
        }
    
    def process_current_session(self, settings, parent_item):
        """
        Base implementation of session processing.
        """
        # Create the session item
        session_item = self._create_session_item(parent_item)
        
        # Set the icon
        icon_path = utils.get_icon_path(self, self.session_icon_name)
        session_item.set_icon_from_path(icon_path)
        
        return session_item
    
    def _create_session_item(self, parent_item):
        """
        Create a session item. Override in subclasses.
        """
        raise NotImplementedError
    
    @property
    def session_icon_name(self):
        """
        Name of the session icon. Override in subclasses.
        """
        raise NotImplementedError
