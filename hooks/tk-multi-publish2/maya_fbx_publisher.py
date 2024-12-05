# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an FBX file from Maya for use in Unreal Engine.
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does.
        """
        return """
        Publishes the current Maya session as an FBX file for use in Unreal Engine.
        The FBX file will include all DAG nodes marked for export.
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
                "description": "Template path for published FBX files. Should "
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
        engine = sgtk.platform.current_engine()

        # Get the path in a normalized state. No trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(item.properties["path"])

        # Ensure the publish folder exists
        publish_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(publish_folder)

        try:
            # Export the FBX file
            self._export_fbx(path)
        except Exception as e:
            self.logger.error("Failed to export FBX file: %s" % e)
            return False

        return True

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed, and can for example
        be used to version up files.
        """
        pass

    def _export_fbx(self, path):
        """
        Export the current Maya scene as an FBX file.
        """
        # Your FBX export code here
        pass
