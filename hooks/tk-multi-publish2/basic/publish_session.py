"""
Hook for publishing the current Unreal Editor session.
"""
import os
import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealSessionPublishPlugin(HookBaseClass):
    """
    Plugin for publishing the current Unreal Editor session.
    """

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does.
        """
        return """
        Publishes the current Unreal Editor session to ShotGrid. This will
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
        return ["unreal.session"]

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
        # Get the current project file path
        project_path = unreal.SystemLibrary.get_project_directory()
        
        # Get the publish template
        publish_template = self.get_publish_template(settings)
        if publish_template:
            publish_path = publish_template.apply_fields({
                "version": item.properties.get("version_number", 1),
                "name": os.path.basename(project_path)
            })
            
            # Ensure the publish folder exists
            publish_folder = os.path.dirname(publish_path)
            self.parent.ensure_folder_exists(publish_folder)
            
            # Save the current project
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
                save_map_packages=True,
                save_content_packages=True
            )

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
