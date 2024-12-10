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
        path = sgtk.util.ShotgunPath.normalize(item.properties["path"])

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

        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        if not asset_path or not asset_name:
            self.logger.debug("Asset path or name not configured.")
            return False

        publish_template = item.properties["publish_template"]

        # Add the Unreal asset name to the fields
        fields = {"name": asset_name}

        # Add today's date to the fields
        date = datetime.date.today()
        fields["YYYY"] = date.year
        fields["MM"] = date.month
        fields["DD"] = date.day

        # Get current context information
        current_entity = item.context.entity
        if current_entity:
            # Asset 정보 추가
            fields["Asset"] = current_entity["code"]
            
            # Asset 타입 가져오기
            asset_info = self.parent.shotgun.find_one(
                "Asset",
                [["id", "is", current_entity["id"]]],
                ["sg_asset_type"]
            )
            if asset_info and asset_info["sg_asset_type"]:
                fields["sg_asset_type"] = asset_info["sg_asset_type"]

        # Step 정보 가져오기
        current_step = item.context.step
        if current_step:
            fields["Step"] = current_step["name"]

        # Version 번호 생성 (여기서는 간단히 1로 설정)
        fields["version"] = 1

        # Stash the Unreal asset path and name in properties
        item.properties["asset_path"] = asset_path
        item.properties["asset_name"] = asset_name

        try:
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

            # run the base class validation
            self.save_ui_settings(settings)
            return True
        except Exception as e:
            self.logger.error(f"Error during validation: {str(e)}")
            return False

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
