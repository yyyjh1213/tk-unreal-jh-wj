import tank
import os
import sys
import datetime
import maya.cmds as cmds
import maya.mel as mel

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = tank.get_hook_baseclass()

# Import unreal module only when in Unreal environment
try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.
    """

    @property
    def description(self):
        return """Publishes the asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk. Other users will be able to access the published file via
        the <b>Loader</b> app so long as they have access to
        the file's location on disk."""

    @property
    def settings(self):
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}
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
        base_settings.update(publish_template_setting)
        return base_settings

    @property
    def item_filters(self):
        return ["unreal.asset.StaticMesh", "maya.session"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        Only items matching the filters defined via the item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here.

        :param settings: Dictionary of Settings. The keys are strings, matching the keys returned in the settings property.
                       The values are `Setting` instances.
        :param item: Item to process

        :returns: dictionary with the following keys:
            - accepted (bool): True if the plugin should accept the item, False otherwise
            - enabled (bool): If True, the plugin will be enabled in the UI, otherwise it will be disabled.
                            Only applies to accepted tasks.
            - visible (bool): If True, the plugin will be visible in the UI, otherwise it will be hidden.
                            Only applies to accepted tasks.
            - checked (bool): If True, the plugin will be checked in the UI, otherwise it will be unchecked.
                            Only applies to accepted tasks.
        """
        # Check if this is a Maya session
        if item.type == "maya.session":
            # Make sure we have meshes in the scene
            import maya.cmds as cmds
            if not cmds.ls(type="mesh"):
                self.logger.warn("No meshes found in the scene")
                return {"accepted": False}
            return {"accepted": True}
        
        # Check if this is an Unreal asset
        if UNREAL_AVAILABLE and item.properties.get("unreal_asset_path"):
            return {"accepted": True}

        return {"accepted": False}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.

        Returns a boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching the keys returned in the settings property.
                       The values are `Setting` instances.
        :param item: Item to process

        :returns: True if item is valid, False otherwise.
        """
        # For Maya sessions, check if we can export FBX
        if item.type == "maya.session":
            import maya.cmds as cmds
            # Check if the scene has any meshes
            if not cmds.ls(type="mesh"):
                self.logger.error("No meshes found in the scene")
                return False
            return True

        # For Unreal assets, validate the asset path
        if UNREAL_AVAILABLE and item.properties.get("unreal_asset_path"):
            return True

        return False

    def _get_next_version_number(self, path_template, fields):
        """
        Find the next available version number for a file.
        
        :param path_template: Template object to use to find next available version
        :param fields: Dictionary of fields for the template
        :returns: The next available version number
        """
        publisher = self.parent
        
        # Find all existing versions
        existing_versions = []
        try:
            for existing_path in publisher.sgtk.paths_from_template(path_template, fields, skip_missing_optional_keys=True):
                existing_fields = path_template.get_fields(existing_path)
                existing_versions.append(existing_fields.get("version", 0))
        except:
            return 1  # If something goes wrong, just return 1
            
        # Find next version
        return max(existing_versions or [0]) + 1

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching the keys returned in the settings property.
                       The values are `Setting` instances.
        :param item: Item to process
        """
        publisher = self.parent
        
        # Get the path in a normalized state
        path = tank.util.ShotgunPath.normalize(item.properties["path"])

        # For Maya sessions, export FBX
        if item.type == "maya.session":
            # Get the configured publish template
            publish_template = publisher.get_template_by_name(settings["Publish Template"].value)
            if not publish_template:
                self.logger.error("Missing publish template in settings")
                return False

            # Get fields from the current session
            work_template = item.properties.get("work_template")
            if not work_template:
                self.logger.error("Work template not found")
                return False

            fields = work_template.get_fields(path)
            
            # Get next version number
            fields["version"] = self._get_next_version_number(publish_template, fields)
            item.properties["publish_version"] = fields["version"]

            # Update with the fields from the context
            fields.update(item.context.as_template_fields(publish_template))

            # Get the publish path
            publish_path = publish_template.apply_fields(fields)

            # Ensure the publish folder exists
            publish_folder = os.path.dirname(publish_path)
            self.parent.ensure_folder_exists(publish_folder)

            # Export FBX
            self._maya_export_fbx(publish_path)

            # Register the publish
            self._register_publish(settings, item, publish_path)

            return True

        # For Unreal assets
        if UNREAL_AVAILABLE and item.properties.get("unreal_asset_path"):
            # Your existing Unreal publish logic here
            pass

        return False

    def _maya_export_fbx(self, publish_path):
        """
        Export the current Maya scene as FBX.

        :param publish_path: The path to export the FBX to
        """
        import maya.cmds as cmds
        import maya.mel as mel

        # Ensure the FBX plugin is loaded
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya")

        # Set FBX export settings
        mel.eval('FBXResetExport')
        mel.eval('FBXExportFileVersion -v FBX201800')
        mel.eval('FBXExportUpAxis y')
        mel.eval('FBXExportShapes -v true')
        mel.eval('FBXExportSkins -v true')
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportSmoothMesh -v true')
        mel.eval('FBXExportTangents -v true')
        mel.eval('FBXExportTriangulate -v false')
        mel.eval('FBXExportConstraints -v false')
        mel.eval('FBXExportCameras -v false')
        mel.eval('FBXExportLights -v false')
        mel.eval('FBXExportEmbeddedTextures -v false')
        mel.eval('FBXExportInputConnections -v false')

        # Export FBX
        mel.eval('FBXExport -f "{}" -s'.format(publish_path.replace('\\', '/')))

    def _register_publish(self, settings, item, path):
        """
        Register the publish using the shotgun api.

        :param settings: Dictionary of Settings. The keys are strings, matching the keys returned in the settings property.
                       The values are `Setting` instances.
        :param item: Item to process
        :param path: Path of the published file
        """
        # Get the publish "type" from the settings or use a default
        publish_type = (settings.get("File Type") or {}).get("value", "FBX File")

        # Update the item properties
        item.properties["publish_type"] = publish_type
        item.properties["path"] = path
        
        # Let the base class register the publish
        super(UnrealAssetPublishPlugin, self).finalize(settings, item)

def _unreal_export_asset_to_fbx(destination_path, asset_path, asset_name):
    """
    Export an asset to FBX from Unreal

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The asset name to use for the FBX filename
    """
    # Create and configure an asset export task
    export_task = _generate_fbx_export_task(destination_path, asset_path, asset_name)

    # Run the export task
    unreal.AssetToolsHelpers.get_asset_tools().export_assets(
        [export_task],
        False  # Don't show the export options dialog
    )

def _generate_fbx_export_task(destination_path, asset_path, asset_name):
    """
    Create and configure an Unreal AssetExportTask

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The FBX filename to export to
    :return the configured AssetExportTask
    """
    # Create an asset export task
    export_task = unreal.AssetExportTask()

    # The asset to export
    export_task.object = unreal.load_asset(asset_path)

    # The name of the file to export to
    export_task.filename = os.path.join(destination_path, "%s.fbx" % asset_name)

    # Replace the file if it exists
    export_task.replace_identical = True

    # Don't auto save the export task settings
    export_task.automated = True

    # Don't show the export options dialog
    export_task.prompt = False

    return export_task
