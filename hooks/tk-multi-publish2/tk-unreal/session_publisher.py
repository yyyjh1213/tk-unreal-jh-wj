"""
Publisher that handles publishing the current Unreal Engine session.
"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealSessionPublisher(HookBaseClass):
    """
    Publisher that publishes the current session to Shotgun.
    """

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin.
        """
        if item.type == "unreal.session":
            return True
            
        return False

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
        Get the path where the session should be saved.
        """
        template = self.get_template_by_name(settings["Publish Template"])
        return template.apply_fields(item.properties)

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
