# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealExporterPlugin(HookBaseClass):
    """
    Plugin for exporting content from Unreal Engine.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate and publish methods.

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
        return {
            "Export Path Template": {
                "type": "template",
                "default": None,
                "description": "Template path for exported content. Should"
                "correspond to a template defined in templates.yml."
            },
        }

    def validate_export(self, settings, item):
        """
        Validates the export settings for a given item.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to validate export settings for
        :returns: True if validation passed, False otherwise.
        """
        path = self._get_save_path(settings, item)
        
        if not path:
            self.logger.error(
                "Export path could not be determined for item: %s" % item.name
            )
            return False

        return True

    def export_content(self, settings, item):
        """
        Execute the export of the content using the supplied settings.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to export
        :returns: Path to the exported content
        """
        # get the path in a normalized state
        path = self._get_save_path(settings, item)
        
        try:
            # TODO: Implement Unreal specific export logic here
            # This could involve:
            # - Exporting static meshes
            # - Exporting skeletal meshes
            # - Exporting animations
            # - Exporting materials
            # - etc.
            pass
            
        except Exception as e:
            self.logger.error(
                "Failed to export content for item: %s. Error: %s" % (item.name, str(e))
            )
            return None

        return path

    def _get_save_path(self, settings, item):
        """
        Get a path for saving the content based on the item and settings.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to determine the save path for
        :returns: Path for saving the item
        """
        publisher = self.parent

        # get the path in a normalized state
        path_template = settings.get("Export Path Template").value
        if not path_template:
            self.logger.error("No export path template defined for item: %s" % item.name)
            return None

        # get fields from the item
        fields = item.properties.get("fields", {})

        # ensure the export folder exists
        try:
            path = publisher.get_template_by_name(path_template)
            path = path.apply_fields(fields)
            path = sgtk.util.ShotgunPath.normalize(path)
            
            destination_folder = os.path.dirname(path)
            self.parent.ensure_folder_exists(destination_folder)
            
            return path
            
        except Exception as e:
            self.logger.error(
                "Failed to get save path for item: %s. Error: %s" % (item.name, str(e))
            )
            return None
