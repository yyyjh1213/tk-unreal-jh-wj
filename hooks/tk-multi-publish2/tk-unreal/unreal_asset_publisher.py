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
        """
        if item.type == "unreal.asset":
            return True
            
        return False

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
        """
        publisher = self.parent
        
        # Get the path to publish
        publish_template = self.get_template_by_name(settings["Publish Template"])
        publish_path = publish_template.apply_fields(item.properties)
        
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
            "published_file_type": settings["Asset Type"]
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
