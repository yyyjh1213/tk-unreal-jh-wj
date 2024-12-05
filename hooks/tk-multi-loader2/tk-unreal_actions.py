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

        Please note that it is perfectly possible to create more than one action "instance" for
        an action! You can for example do scene introspection - if the action passed in
        is "character_attachment" you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action instances:
        "attach to left hand", "attach to right hand" etc. In this case, when more than
        one object is returned for an action, use the params key to pass additional
        data into the run_action hook.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """
        app = self.parent
        app.log_debug("Generate actions called for UI element %s. "
                      "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))

        action_instances = []

        if "import_content" in actions:
            action_instances.append({"name": "import_content",
                                     "params": None,
                                     "caption": "Import into Content Browser",
                                     "description": "This will import the asset into the Unreal Editor Content Browser."})

        return action_instances

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the ``execute_action``
            method for backward compatibility with hooks written for the previous
            version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an error
            is raised midway through.

        :param list actions: Action dictionaries.
        """
        for single_action in actions:
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug("Execute action called for action %s. "
                      "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))

        # resolve path
        path = self.get_publish_path(sg_publish_data)

        if name == "import_content":
            self._import_to_content_browser(path, sg_publish_data)
        else:
            try:
                HookBaseClass.execute_action(self, name, params, sg_publish_data)
            except AttributeError:
                # base class doesn't have the method, so ignore and continue
                pass

    def _import_to_content_browser(self, path, sg_publish_data):
        """
        Import the asset into the Unreal Content Browser.

        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """

        unreal.log("File to import: {}".format(path))

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        destination_path, destination_name = self._get_destination_path_and_name(sg_publish_data)

        asset_path = self._unreal_import_fbx_asset(path, destination_path, destination_name)

        if asset_path:
            self._set_asset_metadata(asset_path, sg_publish_data)

            # Focus the Unreal Content Browser on the imported asset
            asset_paths = []
            asset_paths.append(asset_path)
            unreal.EditorAssetLibrary.sync_browser_to_objects(asset_paths)

    def _set_asset_metadata(self, asset_path, sg_publish_data):
        """
        Set needed metadata on the given asset
        """
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)

        if not asset:
            return

        engine = sgtk.platform.current_engine()

        # Add a metadata tag for "created_by"
        if "created_by" in sg_publish_data:
            createdby_dict = sg_publish_data["created_by"]
            name = ""
            if "name" in createdby_dict:
                name = createdby_dict["name"]
            elif "id" in createdby_dict:
                name = createdby_dict["id"]

            tag = engine.get_metadata_tag("created_by")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, tag, name)

        # Add a metadata tag for the Shotgun URL
        # Construct the PublishedFile URL from the publish data type and id since
        # the context of a PublishedFile is the Project context
        shotgun_site = self.sgtk.shotgun_url
        type = sg_publish_data["type"]
        id = sg_publish_data["id"]
        url = shotgun_site + "/detail/" + type + "/" + str(id)

        """
        # Get the URL from the context (Asset, Task, Project)
        # The context of the publish data is usually the Task (or Project if there's no task)
        # But try to be more specific by using the context of the linked entity (Asset)
        entity_dict = sg_publish_data["entity"]
        context = self.sgtk.context_from_entity_dictionary(entity_dict)
        url = context.shotgun_url

        if entity_dict["type"] == "Project":
            # As a last resort, construct the PublishedFile URL from the publish data type and id since
            # the context of a PublishedFile is the Project context
            shotgun_site = self.sgtk.shotgun_url
            type = sg_publish_data["type"]
            id = sg_publish_data["id"]
            url = shotgun_site + "/detail/" + type + "/" + str(id)
        """

        tag = engine.get_metadata_tag("url")
        unreal.EditorAssetLibrary.set_metadata_tag(asset, tag, url)

        unreal.EditorAssetLibrary.save_loaded_asset(asset)

    def _get_destination_path_and_name(self, sg_publish_data):
        """
        Get the destination path and name from the publish data and the templates

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :return destination_path that matches a template and destination_name from asset or published file
        """
        # Get the publish context
        context = self.sgtk.context_from_entity_dictionary(sg_publish_data)

        # Get the destination templates based on the context
        if context.entity is None or context.entity["type"] != "Asset":
            destination_template = self.sgtk.templates["unreal_loader_project_path"]
            destination_name_template = self.sgtk.templates["unreal_loader_project_name"]
        else:
            destination_template = self.sgtk.templates["unreal_loader_asset_path"]
            destination_name_template = self.sgtk.templates["unreal_loader_asset_name"]

        # Initialize fields dictionary
        fields = {}
        
        # Get project info
        if context.project:
            fields["project"] = context.project["name"]

        # Get asset info from entity
        if context.entity and context.entity["type"] == "Asset":
            entity = context.entity
            
            # Get asset type
            if "sg_asset_type" in entity:
                fields["asset_type"] = entity["sg_asset_type"]
            
            # Get asset name
            if "code" in entity:
                fields["asset_name"] = entity["code"]
        
        # Get step info from task
        if context.task:
            step = context.task["step"]
            if step and "short_name" in step:
                fields["step"] = step["short_name"]

        # Get destination path
        try:
            destination_path = destination_template.apply_fields(fields)
        except Exception as e:
            self.logger.warning(f"Error applying fields to path template: {e}")
            destination_path = "/Game/Assets/"

        # Get destination name
        try:
            destination_name = destination_name_template.apply_fields(fields)
        except Exception as e:
            self.logger.warning(f"Error applying fields to name template: {e}")
            if "asset_name" in fields:
                destination_name = self._sanitize_name(fields["asset_name"])
            else:
                destination_name = self._sanitize_name(sg_publish_data.get("code", ""))

        return destination_path, destination_name

    def _get_fbx_metadata(self, sg_publish_data):
        """
        FBX 파일의 ShotGrid 메타데이터 정보를 가져옵니다.
        
        :param sg_publish_data: ShotGrid publish data dictionary
        :return: 메타데이터 정보를 담은 dictionary
        """
        metadata = {
            "name": sg_publish_data.get("name", ""),
            "version": sg_publish_data.get("version_number", 0),
            "task": sg_publish_data.get("task.Task.content", ""),
            "entity": sg_publish_data.get("entity.Asset.code", ""),
            "project": sg_publish_data.get("project.Project.name", ""),
            "created_by": sg_publish_data.get("created_by.HumanUser.name", ""),
            "created_at": sg_publish_data.get("created_at", ""),
            "description": sg_publish_data.get("description", "")
        }
        return metadata

    def _display_metadata(self, metadata):
        """
        메타데이터 정보를 Unreal 에디터에 표시합니다.
        
        :param metadata: 메타데이터 dictionary
        """
        message = f"""
        Asset Information:
        - Name: {metadata['name']}
        - Version: {metadata['version']}
        - Task: {metadata['task']}
        - Entity: {metadata['entity']}
        - Project: {metadata['project']}
        - Created By: {metadata['created_by']}
        - Created At: {metadata['created_at']}
        - Description: {metadata['description']}
        """
        
        unreal.log_warning(message)
        
        # Unreal 에디터에 노티피케이션 표시
        notification = unreal.EditorNotification()
        notification.text = f"Imported: {metadata['name']} (v{metadata['version']})"
        notification.image = None
        notification.fade_in_duration = 0.5
        notification.fade_out_duration = 0.5
        notification.expire_duration = 5.0
        unreal.EditorNotificationUtils.add_notification(notification)

    def _unreal_import_fbx_asset(self, input_path, destination_path, destination_name):
        """
        Import an FBX into Unreal Content Browser

        :param input_path: The fbx file to import
        :param destination_path: The Content Browser path where the asset will be placed
        :param destination_name: The asset name to use; if None, will use the filename without extension
        """
        import_task = self._generate_fbx_import_task(input_path, destination_path, destination_name)
        
        try:
            # FBX 임포트 실행
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])
            imported_assets = import_task.get_editor_property("imported_object_paths")
            
            if imported_assets:
                # 메타데이터 표시
                metadata = self._get_fbx_metadata(self.parent.sg_publish_data)
                self._display_metadata(metadata)
                
                return imported_assets[0]
        except Exception as e:
            unreal.log_error(f"Failed to import FBX: {str(e)}")
            return None

    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behaviour of things

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
        task.filename = filename
        task.destination_path = destination_path

        # By default, destination_name is the filename without the extension
        if destination_name is not None:
            task.destination_name = destination_name

        task.replace_existing = replace_existing
        task.automated = automated
        task.save = save

        task.options = unreal.FbxImportUI()
        task.options.import_materials = materials
        task.options.import_textures = textures
        task.options.import_as_skeletal = as_skeletal
        # task.options.static_mesh_import_data.combine_meshes = True

        task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        if as_skeletal:
            task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH

        return task


"""
Functions to import FBX into Unreal
"""


def _sanitize_name(name):
    # Remove the default Shotgun versioning number if found (of the form '.v001')
    name_no_version = re.sub(r'.v[0-9]{3}', '', name)

    # Replace any remaining '.' with '_' since they are not allowed in Unreal asset names
    return name_no_version.replace('.', '_')


def _unreal_import_fbx_asset(input_path, destination_path, destination_name):
    """
    Import an FBX into Unreal Content Browser

    :param input_path: The fbx file to import
    :param destination_path: The Content Browser path where the asset will be placed
    :param destination_name: The asset name to use; if None, will use the filename without extension
    """
    tasks = []
    tasks.append(_generate_fbx_import_task(input_path, destination_path, destination_name))

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    first_imported_object = None

    for task in tasks:
        unreal.log("Import Task for: {}".format(task.filename))
        for object_path in task.imported_object_paths:
            unreal.log("Imported object: {}".format(object_path))
            if not first_imported_object:
                first_imported_object = object_path

    return first_imported_object


def _generate_fbx_import_task(
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
    task.filename = filename
    task.destination_path = destination_path

    # By default, destination_name is the filename without the extension
    if destination_name is not None:
        task.destination_name = destination_name

    task.replace_existing = replace_existing
    task.automated = automated
    task.save = save

    task.options = unreal.FbxImportUI()
    task.options.import_materials = materials
    task.options.import_textures = textures
    task.options.import_as_skeletal = as_skeletal
    # task.options.static_mesh_import_data.combine_meshes = True

    task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    if as_skeletal:
        task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH

    return task