# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealAssetPublisherPlugin(HookBaseClass):
    """
    Plugin for publishing Unreal assets to ShotGrid.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate and publish methods.
        """
        # Inherit base settings
        base_settings = super(UnrealAssetPublisherPlugin, self).settings

        # Add Unreal specific settings
        unreal_settings = {
            "Asset Type": {
                "type": "string",
                "default": "StaticMesh",
                "description": "Type of Unreal asset to publish (StaticMesh, SkeletalMesh, etc.)"
            },
            "Content Path": {
                "type": "string",
                "default": "/Game/Assets",
                "description": "Path in the Unreal content browser where the asset will be saved"
            }
        }

        return dict(list(base_settings.items()) + list(unreal_settings.items()))

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: Accepted (boolean) and Accepted reason (str)
        """
        if item.type == "unreal.asset":
            return True, "Unreal asset item accepted."

        return False, "Item not of type unreal.asset"

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """
        publisher = self.parent
        path = item.properties.get("path")
        
        if not path:
            self.logger.error("No path found for item: %s" % item.name)
            return False

        if not os.path.exists(path):
            self.logger.error("Path does not exist: %s" % path)
            return False

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        publisher = self.parent
        path = item.properties.get("path")

        # Get the path in a normalized state
        path = sgtk.util.ShotgunPath.normalize(path)

        try:
            # TODO: Implement Unreal specific publish logic here
            # This could involve:
            # - Importing the asset into Unreal
            # - Setting up materials
            # - Configuring asset properties
            # - etc.
            self._import_asset_to_unreal(path, settings, item)
            
            # Let the base class register the publish
            super(UnrealAssetPublisherPlugin, self).publish(settings, item)
            
        except Exception as e:
            self.logger.error(
                "Failed to publish Unreal asset for item: %s. Error: %s" % (item.name, str(e))
            )
            return None

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        # TODO: Implement any post-publish operations
        # For example:
        # - Cleanup temporary files
        # - Update asset references
        # - etc.
        pass

    def _import_asset_to_unreal(self, path, settings, item):
        """
        Helper method to import an asset into Unreal Engine.

        :param path: Path to the asset file
        :param settings: Publisher settings
        :param item: Item being published
        """
        asset_type = settings.get("Asset Type").value
        content_path = settings.get("Content Path").value

        # TODO: Implement asset import logic based on asset_type
        # This could use the Unreal Python API to:
        # - Import different types of assets (StaticMesh, SkeletalMesh, etc.)
        # - Set up materials and textures
        # - Configure asset properties
        pass
