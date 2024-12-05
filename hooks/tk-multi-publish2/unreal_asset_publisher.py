# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import unreal
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing Unreal assets.
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does.
        """
        return """
        Publishes the selected Unreal assets to ShotGrid. A <b>Publish</b> entry will be
        created in ShotGrid which will include a reference to the asset. The asset
        will be exported to the project's publish folder.
        """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.
        """
        return {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published assets. Should "
                             "correspond to a template defined in templates.yml.",
            }
        }

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.
        """
        return True

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

        # Get the path in a normalized state. No trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(item.properties["path"])

        # Ensure the publish folder exists
        publish_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(publish_folder)

        try:
            self._publish_asset(path, item)
        except Exception as e:
            self.logger.error("Failed to publish asset: %s" % e)
            return False

        return True

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed, and can for example
        be used to version up files.
        """
        pass

    def _publish_asset(self, path, item):
        """
        Publish the Unreal asset and register with ShotGrid.
        """
        publisher = self.parent
        
        # Export the asset
        asset_path = item.properties.get("unreal_asset_path")
        if asset_path:
            # Export the asset using Unreal's asset registry
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
            asset = asset_registry.get_asset_by_object_path(asset_path)
            if asset:
                unreal.EditorAssetLibrary.export_asset(asset_path, path)
            else:
                self.logger.error("Could not find asset: %s" % asset_path)
                return False
        
        # Create the publish
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": os.path.basename(path),
            "created_by": sgtk.util.get_current_user(publisher.sgtk),
            "version_number": publisher.util.get_version_number(path),
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": "Unreal Asset"
        }

        # Create the publish and stash it in the item properties for other
        # plugins to use.
        item.properties["sg_publish_data"] = sgtk.util.register_publish(**publish_data)
