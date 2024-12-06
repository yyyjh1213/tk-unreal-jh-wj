"""
Hook for publishing the current Maya session in Unreal Engine context.
"""
import os
import sgtk
import maya.cmds as cmds

HookBaseClass = sgtk.get_hook_baseclass()

class MayaUnrealSessionPublishPlugin(HookBaseClass):
    """
    Plugin for publishing the current Maya session for Unreal Engine.
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does.
        """
        return """
        Publishes the current Maya session to ShotGrid. This will
        create a new version entry in ShotGrid which will include a reference
        to the current session's project file.
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
                "description": "Template path for published work files. Should "
                             "correspond to a template defined in "
                             "templates.yml.",
            }
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["maya.session"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin.
        
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: dictionary with the following keys:
            - accepted (bool): Indicates if the plugin is interested in this value
            - enabled (bool): If True, the plugin will be enabled in the UI,
                otherwise it will be disabled. Optional, True by default.
            - checked (bool): If True, the plugin will be checked in the UI,
                otherwise it will be unchecked. Optional, True by default.
        """
        if item.type == "maya.session":
            return {
                "accepted": True,
                "enabled": True,
                "checked": True
            }
            
        return {
            "accepted": False,
            "enabled": False,
            "checked": False
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        # Get the current Maya file path
        maya_file_path = cmds.file(query=True, sceneName=True)
        
        # Get the publish template
        publish_template = self.get_publish_template(settings)
        if publish_template:
            publish_path = publish_template.apply_fields({
                "version": item.properties.get("version_number", 1),
                "name": os.path.basename(maya_file_path)
            })
            
            # Ensure the publish folder exists
            publish_folder = os.path.dirname(publish_path)
            self.parent.ensure_folder_exists(publish_folder)
            
            # Save the current Maya file
            cmds.file(save=True, type='mayaAscii')

            # Register the publish
            self.parent.register_publish(
                publish_path,
                item.name,
                item.properties.get("version_number", 1),
                item.description
            )

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once
        all the publish tasks have completed, and can for example
        be used to version up files.
        """
        pass
