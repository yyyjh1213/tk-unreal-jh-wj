import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an FBX file from a Maya session.
    """

    @property
    def description(self):
        return """
        Export the current Maya scene as an FBX file.
        """

    @property
    def settings(self):
        return {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published FBX files."
            }
        }

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        """
        return True

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        path = self._get_publish_path(settings, item)
        
        if not path:
            self.logger.error("Publish template not found!")
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publish_path = self._get_publish_path(settings, item)
        
        if not os.path.exists(os.path.dirname(publish_path)):
            os.makedirs(os.path.dirname(publish_path))

        # Export the FBX file
        cmds.file(publish_path, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
        
        self.logger.info("FBX file published to: %s" % publish_path)

        # Register the publish
        self._register_publish(settings, item, publish_path)

    def _get_publish_path(self, settings, item):
        """
        Get the publish path for the FBX file.
        """
        publish_template = settings.get("Publish Template")
        publisher = self.parent

        # Get the template from the settings
        publish_template = publisher.get_template_by_name(publish_template)
        if not publish_template:
            return None

        # Get fields from the current session
        fields = {}
        
        # Update fields with the item's fields
        fields.update(item.properties.get("fields", {}))

        # Update with any fields from the context
        fields.update(item.context.as_template_fields(publish_template))

        path = publish_template.apply_fields(fields)
        return path

    def _register_publish(self, settings, item, path):
        """
        Register the published file with Flow Production Tracking.
        """
        publisher = self.parent
        
        # Get the publish info
        publish_version = publisher.util.get_version_number(path)
        publish_name = publisher.util.get_publish_name(path)
        
        # Register the publish using the base class' register_publish method
        self.parent.register_publish(
            item,
            path,
            publish_name,
            publish_version,
        )
