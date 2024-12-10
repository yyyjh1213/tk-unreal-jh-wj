"""
Publisher that handles publishing the current Unreal Engine session.
"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealSessionPublisher(HookBaseClass):
    """
    Publisher that publishes the current session to Shotgun.
    """

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["unreal.session"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin.
        
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: dictionary with the following keys:
            - accepted (bool): Indicates if the plugin is interested in this value
            - enabled (bool): If True, the plugin will be enabled in the UI,
                otherwise it will be disabled. Optional, True by default.
            - checked (bool): If True, the plugin will be checked in the UI,
                otherwise it will be unchecked. Optional, True by default.
        """
        if item.type == "unreal.session":
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
        publisher = self.parent
        engine = publisher.engine
        
        # Get the path to save
        path = self._get_save_path(settings, item)
        
        # Save the current session
        engine.save_current_level(path)
        
        # Register the publish
        self._register_publish(settings, item, path)
        
        return True

    def _get_save_path(self, settings, item):
        """
        Get the path to save the current session.
        
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: Path to save the current session
        """
        publisher = self.parent
        
        # Get the template from the settings
        template_name = settings.get("Publish Template").value
        if not template_name:
            raise ValueError("'Publish Template' not found in settings!")
            
        # Get the templates from the publisher
        templates = publisher.sgtk.templates
        template = templates.get(template_name)
        
        if template is None:
            raise ValueError("Template '%s' not found!" % template_name)
            
        # Get fields from the current context
        fields = publisher.context.as_template_fields(template)
        
        # Add version if not set
        if "version" not in fields:
            fields["version"] = 1
            
        # Add name if not set
        if "name" not in fields and hasattr(item, "properties"):
            fields["name"] = item.properties.get("name", "session")
            
        # Apply fields to template to get the publish path
        path = template.apply_fields(fields)
        return path

    def _register_publish(self, settings, item, path):
        """
        Register the publish with Shotgun.
        """
        publisher = self.parent
        
        # Create the publish
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": item.name,
            "version_number": item.properties.get("version_number", 1),
            "thumbnail_path": item.get_thumbnail_as_path(),
        }
        
        # Register the publish using the base class' utility method
        super(UnrealSessionPublisher, self)._register_publish(**publish_data)
