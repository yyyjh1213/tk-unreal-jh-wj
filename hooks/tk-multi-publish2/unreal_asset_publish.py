# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import sgtk
import os
import sys
import unreal
import datetime

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{config}/tk-multi-publish2/unreal_asset_publish.py"
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does.
        """
        return """Publishes the asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk. Other users will be able to access the published file via
        the <b>Loader</b> app so long as they have access to
        the file's location on disk."""

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}

        # Here you can add any additional settings specific to this plugin
        publish_template_setting = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            },
            "Publish Folder": {
                "type": "string",
                "default": None,
                "description": "Optional folder to use as a root for publishes"
            },
        }

        # update the base settings
        base_settings.update(publish_template_setting)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["unreal.asset.StaticMesh"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        Only items matching the filters defined via the item_filters property will be presented to this method.
        
        A publish task will be generated for each item accepted here. Returns a dictionary with the following booleans:
            accepted: Indicates if the plugin is interested in this value at all. Required.
            enabled: If True, the plugin will be enabled in the UI, otherwise it will be disabled. Optional, True by default.
            visible: If True, the plugin will be visible in the UI, otherwise it will be hidden. Optional, True by default.
            checked: If True, the plugin will be checked in the UI, otherwise it will be unchecked. Optional, True by default.
        """
        
        # Get the path in a normalized state
        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        
        if not asset_path or not asset_name:
            self.logger.warn("Asset path or name not found for item")
            return {"accepted": False}
            
        # Set the path on the item properties - this is needed by the base plugin
        item.properties["path"] = asset_path
        
        # Get publish template from settings
        publish_template = self.get_publish_template(settings, item)
        if publish_template:
            item.properties["publish_template"] = publish_template
        
        return {
            "accepted": True,
            "checked": True
        }

    def get_publish_template(self, settings, item):
        """
        Get the publish template from the settings.
        """
        # Get the template from the settings
        publish_template = settings.get("Publish Template").value
        if not publish_template:
            self.logger.debug(
                "No publish template defined for item: %s" % item.name
            )
            return None

        return self.parent.engine.get_template_by_name(publish_template)

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        if not asset_path or not asset_name:
            self.logger.debug("Asset path or name not configured.")
            return False

        publish_template = item.properties["publish_template"]

        # Add the Unreal asset name to the fields
        fields = {"name": asset_name}

        # Get the current context from ShotGrid
        context = self.parent.context
        
        # Add required template fields from context
        fields["Asset"] = context.entity["name"] if context.entity else None
        fields["sg_asset_type"] = context.entity["sg_asset_type"] if context.entity else None
        fields["Step"] = context.step["name"] if context.step else None
        
        # Add version number - you may want to customize this logic
        fields["version"] = 1  # Default to version 1, or implement version detection
        
        # Add today's date to the fields
        date = datetime.date.today()
        fields["YYYY"] = date.year
        fields["MM"] = date.month
        fields["DD"] = date.day

        # Validate required fields
        required_fields = ["Asset", "sg_asset_type", "Step", "version"]
        missing_fields = []
        
        for field in required_fields:
            if not fields.get(field):
                missing_fields.append(field)
                
        if missing_fields:
            self.logger.warning(
                "Missing required ShotGrid fields for publish template: %s" % ", ".join(missing_fields),
                extra={
                    "action_button": {
                        "label": "Review in ShotGrid",
                        "tooltip": "Open ShotGrid to configure the required fields",
                        "callback": lambda: self.parent.engine.show_panel("tk-multi-shotgunpanel")
                    }
                }
            )
            return False

        # Stash the Unreal asset path and name in properties
        item.properties["asset_path"] = asset_path
        item.properties["asset_name"] = asset_name

        # Get destination path for exported FBX from publish template
        publish_path = publish_template.apply_fields(fields)
        publish_path = os.path.normpath(publish_path)
        if not os.path.isabs(publish_path):
            # If the path is not absolute, prepend the publish folder setting.
            publish_folder = settings["Publish Folder"].value
            if not publish_folder:
                publish_folder = unreal.Paths.project_saved_dir()
            publish_path = os.path.abspath(
                os.path.join(
                    publish_folder,
                    publish_path
                )
            )
        item.properties["publish_path"] = publish_path
        item.properties["path"] = publish_path

        # Remove the filename from the publish path
        destination_path = os.path.dirname(publish_path)

        # Stash the destination path in properties
        item.properties["destination_path"] = destination_path

        # Set the Published File Type
        item.properties["publish_type"] = "Unreal FBX"

        self.save_ui_settings(settings)
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        destination_path = item.properties["destination_path"]
        asset_path = item.properties["asset_path"]
        asset_name = item.properties["asset_name"]

        # Ensure the destination path exists
        self._ensure_destination_path_exists(destination_path)

        # Export the asset to FBX
        self._unreal_export_asset_to_fbx(destination_path, asset_path, asset_name)

        # Let the base class register the publish
        super(UnrealAssetPublishPlugin, self).publish(settings, item)

    def _ensure_destination_path_exists(self, destination_path):
        """
        Ensures the destination path exists by creating it if it doesn't.
        """
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

    def _unreal_export_asset_to_fbx(self, destination_path, asset_path, asset_name):
        """
        Export the asset to FBX using Unreal's export functionality.
        """
        # Create and configure the export task
        export_task = self._generate_fbx_export_task(destination_path, asset_path, asset_name)
        
        # Execute the export task
        unreal.AssetToolsHelpers.get_asset_tools().export_assets([export_task])

    def _generate_fbx_export_task(self, destination_path, asset_path, asset_name):
        """
        Generate an FBX export task for the given asset.
        """
        export_task = unreal.AssetExportTask()
        export_task.object = unreal.load_asset(asset_path)
        export_task.filename = os.path.join(destination_path, f"{asset_name}.fbx")
        export_task.selected = False
        export_task.replace_identical = True
        export_task.prompt = False
        export_task.automated = True
        
        return export_task
