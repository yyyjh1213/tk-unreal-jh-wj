# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import tank
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


HookBaseClass = tank.get_hook_baseclass()


class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    To learn more about writing a publisher plugin, visit
    http://developer.shotgunsoftware.com/tk-multi-publish2/plugin.html
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
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

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
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

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["unreal.asset.StaticMesh"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        # Get the publish template from the settings
        publish_template = settings["Publish Template"].value
        if publish_template:
            item.properties["publish_template"] = publish_template
            self.logger.debug("Using publish template: %s" % publish_template)
        else:
            self.logger.debug("No publish template set")
            return {"accepted": False}

        # Get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = tank.util.ShotgunPath.normalize(item.properties["path"])

        # If there is an item source, apply the source to the item properties
        item_info = item.properties.get("item_info", {})
        item_source = item_info.get("source", None)
        if item_source:
            item.properties["source"] = item_source

        return {
            "accepted": True,
            "checked": True
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """
        # context 정보 확인
        context = item.context

        # Asset 확인
        if not context.entity or context.entity["type"] != "Asset":
            self.logger.error("Asset context is required for publishing")
            return False

        # Template fields 확인
        publish_template = item.properties["publish_template"]
        if not publish_template:
            self.logger.error("No publish template defined")
            return False

        # Asset 정보 확인
        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        if not asset_path or not asset_name:
            self.logger.error("Asset path or name not configured")
            return False

        # Template fields 구성
        fields = {
            "name": asset_name,
            "Asset": context.entity["name"],
            "Step": context.step["name"] if context.step else None,
            "version": 1  # 기본값
        }

        # Template fields 유효성 검사
        try:
            publish_template.validate_and_get_fields(fields)
        except Exception as e:
            self.logger.error("Template validation failed: %s" % str(e))
            return False

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # Ensure that the destination path exists before exporting since the
        # unreal API doesn't handle this.
        destination_path = item.properties["destination_path"]
        self.parent.ensure_folder_exists(destination_path)

        # Export the asset to FBX
        _unreal_export_asset_to_fbx(
            destination_path,
            item.properties["asset_path"],
            item.properties["asset_name"]
        )

        # Let the base class register the publish
        super(UnrealAssetPublishPlugin, self).publish(settings, item)

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        # Do the base class finalization
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
