"""
Hook for publishing Maya FBX files to Unreal Engine.
"""
import os
import sgtk
from . import maya_fbx_unreal_export

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing Maya FBX files to Shotgrid and Unreal Engine.
    """

    @property
    def name(self):
        """The name of this plugin."""
        return "Publish Maya FBX to Unreal"

    @property
    def description(self):
        """The description of this plugin."""
        return "Publish the Maya scene as an FBX file optimized for Unreal Engine."

    @property
    def settings(self):
        """The plugin settings."""
        # Combine settings from both plugins
        base_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published files. Should correspond to a template defined in templates.yml.",
            }
        }
        
        # Get export settings from the exporter
        exporter = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin(self.parent)
        base_settings.update(exporter.settings)
        
        return base_settings

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        """
        return item.type == "maya.fbx.unreal"

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        path = item.properties.get("path", "")
        
        if not path:
            self.logger.error("No path found for item")
            return False
            
        # Create exporter instance for validation
        exporter = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin(self.parent)
        if not exporter.validate(settings, item):
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent
        
        # Get the path in a normalized state
        path = item.properties["path"]
        path = sgtk.util.ShotgunPath.normalize(path)
        
        # Ensure the publish folder exists
        publish_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(publish_folder)
        
        # Export the FBX file using our exporter
        exporter = maya_fbx_unreal_export.MayaFBXUnrealExportPlugin(self.parent)
        if not exporter.export_fbx(settings, item):
            self.logger.error("Failed to export FBX file")
            return False
        
        # Register the published file
        self._register_publish(settings, item, path)
        
        return True

    def _register_publish(self, settings, item, path):
        """
        Register the published file with Shotgun.
        """
        publisher = self.parent
        
        # Get the publish info
        publish_version = publisher.util.get_version_number(path)
        publish_name = publisher.util.get_publish_name(path)
        
        # Create the publish
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": publish_name,
            "version_number": publish_version,
            "published_file_type": "FBX File",
        }
        
        # Register the publish using the base class implementation
        super(MayaFBXPublishPlugin, self)._register_publish(settings, item, path)