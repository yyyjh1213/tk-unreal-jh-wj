"""
Hook for publishing Unreal Engine assets to Shotgun.
"""
import sgtk
import os

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealAssetPublisher(HookBaseClass):
    """
    Hook for publishing Unreal Engine assets to Shotgun.
    """

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["unreal.asset"]

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
        if item.type == "unreal.asset":
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
        # Make sure we have a content path
        content_path = settings.get("Content Path")
        if not content_path:
            self.logger.warning("No content path specified in settings")
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if publish was successful, False otherwise
        """
        publisher = self.parent
        
        # Get the template from the settings
        template_name = settings["Publish Template"].value
        
        # Get the templates from the publisher
        templates = publisher.sgtk.templates
        template = templates[template_name]
        
        if template is None:
            raise ValueError("Template '%s' not found!" % template_name)
            
        # Get fields from the current context
        fields = publisher.context.as_template_fields(template)
        
        # Update fields with item properties
        fields.update(item.properties)
        
        # Apply fields to template to get the publish path
        publish_path = template.apply_fields(fields)
        
        # Ensure the publish folder exists
        self._ensure_folder_exists(publish_path)
        
        # Register the publish
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": publish_path,
            "name": item.name,
            "version_number": item.properties.get("version_number", 1),
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": settings["Asset Type"].value
        }
        
        # Register the publish using the base class' utility method
        super(UnrealAssetPublisher, self)._register_publish(**publish_data)
        
        return True

    def _ensure_folder_exists(self, path):
        """
        Ensure the folder exists for the given path.
        """
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
