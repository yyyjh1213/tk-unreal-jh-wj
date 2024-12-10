# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

"""
Hook that loads defines all the available actions, broken down by publish type.
"""

import os
import sgtk
import unreal
import re

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealActions(HookBaseClass):

    ##############################################################################################################
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions menu for a publish.

        The mapping between Publish types and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the loader app
        has already established *which* actions are appropriate for this object.

        The hook should return at least one action for each item passed in via the
        actions parameter.

        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.

        Because you are operating on a particular publish, you may tailor the output
        (caption, tooltip etc) to contain custom information suitable for this publish.

        The ui_area parameter is a string and indicates where the publish is to be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.
        """

        # get the existing action instances
        action_instances = super(UnrealActions, self).generate_actions(
            sg_publish_data, actions, ui_area
        )

        if "import_content" in actions:
            action_instances.append({
                "name": "import_content",
                "params": None,
                "caption": "Import Content",
                "description": "Import the content into the current Unreal project."
            })

        if "import_level" in actions:
            action_instances.append({
                "name": "import_level",
                "params": None,
                "caption": "Import as Level",
                "description": "Import the content as a new level into the current Unreal project."
            })

        return action_instances

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """

        # resolve path
        # toolkit uses utf-8 encoded strings internally and Maya API expects unicode
        # so convert the path to ensure filenames containing complex characters are supported
        path = self.get_publish_path(sg_publish_data).replace("/", os.path.sep)

        if name == "import_content":
            self._import_content(path, sg_publish_data)

        if name == "import_level":
            self._import_level(path, sg_publish_data)

    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behavior of import and export

    def _import_content(self, path, sg_publish_data):
        """
        Import content into the current Unreal project.

        :param path: Path to the file to import.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Get target path in Unreal
        destination_path = "/Game/Assets"

        # ensure the destination path exists in Unreal
        try:
            unreal.EditorAssetLibrary.make_directory(destination_path)
        except Exception as e:
            self.logger.warning("Failed to create directory: %s" % str(e))

        # Import the file into Unreal
        try:
            self._unreal_import_fbx_asset(path, destination_path, None)
        except Exception as e:
            raise Exception("Failed to import file: %s" % str(e))

    def _import_level(self, path, sg_publish_data):
        """
        Import content as a new level into the current Unreal project.

        :param path: Path to the file to import.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Get target path in Unreal
        destination_path = "/Game/Levels"

        # ensure the destination path exists in Unreal
        try:
            unreal.EditorAssetLibrary.make_directory(destination_path)
        except Exception as e:
            self.logger.warning("Failed to create directory: %s" % str(e))

        # Import the file into Unreal
        try:
            self._unreal_import_fbx_asset(path, destination_path, None)
        except Exception as e:
            raise Exception("Failed to import file: %s" % str(e))

    ##############################################################################################################
    # helper methods

    def _sanitize_name(self, name):
        """
        Sanitize a name for use in Unreal

        :param name: The name to sanitize
        :return: The sanitized name
        """
        # Remove any non-alphanumeric characters except underscore
        name = re.sub(r'[^\w\d]', '_', name)
        
        # Ensure the name starts with a letter or underscore
        if not name[0].isalpha() and name[0] != '_':
            name = '_' + name
            
        return name

    def _unreal_import_fbx_asset(self, input_path, destination_path, destination_name):
        """
        Import an FBX into Unreal Content Browser

        :param input_path: The fbx file to import
        :param destination_path: The Content Browser path where the asset will be placed
        :param destination_name: The asset name to use; if None, will use the filename without extension
        """
        import_task = self._generate_fbx_import_task(
            input_path,
            destination_path,
            destination_name
        )
        
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])
        
        imported_assets = import_task.get_editor_property("imported_object_paths")
        if not imported_assets:
            raise Exception("Failed to import FBX file")

    def _generate_fbx_import_task(
        self,
        filename,
        destination_path,
        destination_name=None,
        replace_existing=True,
        automated=True,
        save=True,
        materials=True,
        textures=True,
        as_skeletal=False
    ):
        """
        Create and configure an Unreal AssetImportTask

        :param filename: The fbx file to import
        :param destination_path: The Content Browser path where the asset will be placed
        :return the configured AssetImportTask
        """
        task = unreal.AssetImportTask()
        
        # Configure the task
        task.set_editor_property("automated", automated)
        task.set_editor_property("destination_name", destination_name)
        task.set_editor_property("destination_path", destination_path)
        task.set_editor_property("filename", filename)
        task.set_editor_property("replace_existing", replace_existing)
        task.set_editor_property("save", save)
        
        # Configure the options
        options = unreal.FbxImportUI()
        
        # Set import mesh
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_textures", textures)
        options.set_editor_property("import_materials", materials)
        options.set_editor_property("import_as_skeletal", as_skeletal)
        
        # Static mesh options
        static_mesh_options = unreal.FbxStaticMeshImportData()
        static_mesh_options.set_editor_property("combine_meshes", True)
        static_mesh_options.set_editor_property("generate_lightmap_u_vs", True)
        options.set_editor_property("static_mesh_import_data", static_mesh_options)
        
        # Set the options
        task.set_editor_property("options", options)
        
        return task
