# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class BaseExporterPlugin(HookBaseClass):
    """
    Base exporter plugin class that provides common functionality for
    exporting content from DCC tools.
    """

    def validate_export(self, settings, item):
        """
        Validate the export settings for a given item.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to validate export settings for
        :returns: True if validation passed, False otherwise.
        """
        raise NotImplementedError

    def export_content(self, settings, item):
        """
        Execute the export of the content using the supplied settings.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to export
        :returns: Path to the exported content
        """
        raise NotImplementedError

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
        path = sgtk.util.ShotgunPath.normalize(path)

        # ensure the export folder exists
        destination_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(destination_folder)

        return path
