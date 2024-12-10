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
        Analyzes the current session and creates publishable items.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
    
    def process_file(self, settings, parent_item, path):
        """
        Analyzes the given file and creates publishable items.
        Can be implemented by subclasses if needed.
        """
        return None
