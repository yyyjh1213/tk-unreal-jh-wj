# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class BasePublisherPlugin(HookBaseClass):
    """
    Base publisher plugin class that provides common functionality for
    publishing content to ShotGrid.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate and publish methods.
        """
        return {
            "Publish Type": {
                "type": "string",
                "default": "File",
                "description": "ShotGrid publish type for the item"
            },
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published files. Should"
                "correspond to a template defined in templates.yml."
            }
        }

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: Accepted (boolean) and Accepted reason (str)
        """
        raise NotImplementedError

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """
        raise NotImplementedError

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        raise NotImplementedError

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed.
        Should be implemented by derived classes.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        raise NotImplementedError
