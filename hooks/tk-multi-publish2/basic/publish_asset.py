import tank
import os
import sys
import unreal
import datetime
import maya.cmds as cmds
import maya.mel as mel

# Local storage path field for known Oses.
_OS_LOCAL_STORAGE_PATH_FIELD = {
    "darwin": "mac_path",
    "win32": "windows_path",
    "linux": "linux_path",
    "linux2": "linux_path",
}[sys.platform]

HookBaseClass = tank.get_hook_baseclass()

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.
    """

    @property
    def description(self):
        return """Publishes the asset to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the exported asset's current
        path on disk. Other users will be able to access the published file via
        the <b>Loader</b> app so long as they have access to
        the file's location on disk."""

    @property
    def settings(self):
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}
        publish_template_setting = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            },
            "Publish Folder": {
                "type": "string",
                "default": None,
                "description": "Optional folder to use as a root for publishes"
            },
        }
        base_settings.update(publish_template_setting)
        return base_settings

    @property
    def item_filters(self):
        return ["unreal.asset.StaticMesh", "maya.session"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any interest to this plugin.
        """
        if item.type == "maya.session":
            # Maya 세션인 경우 메시가 있는지 확인
            meshes = cmds.ls(type="mesh", long=True)
            if not meshes:
                self.logger.warning("No meshes found in the Maya scene")
                return {"accepted": False}
            
            # 메시 정보를 item properties에 저장
            item.properties["meshes"] = meshes
            return {
                "accepted": True,
                "checked": True
            }

        # Get the publish template from the settings
        publish_template = settings["Publish Template"].value
        if publish_template:
            item.properties["publish_template"] = publish_template
            self.logger.debug("Using publish template: %s" % publish_template)
        else:
            self.logger.debug("No publish template set")
            return {"accepted": False}

        path = tank.util.ShotgunPath.normalize(item.properties["path"])
        item_info = item.properties.get("item_info", {})
        item_source = item_info.get("source", None)
        if item_source:
            item.properties["source"] = item_source

        return {
            "accepted": True,
            "checked": True
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        if item.type == "maya.session":
            # Maya 세션 유효성 검사
            if not item.properties.get("meshes"):
                self.logger.error("No meshes found to export")
                return False
            return True

        # Unreal 에셋 유효성 검사
        context = item.context
        if not context.entity or context.entity["type"] != "Asset":
            self.logger.error("Asset context is required for publishing")
            return False

        publish_template = item.properties["publish_template"]
        if not publish_template:
            self.logger.error("No publish template defined")
            return False

        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        if not asset_path or not asset_name:
            self.logger.error("Asset path or name not configured")
            return False

        fields = {
            "name": asset_name,
            "Asset": context.entity["name"],
            "Step": context.step["name"] if context.step else "",
            "version": 1,  # 기본값
        }

        try:
            publish_template.validate_and_get_fields(fields)
        except Exception as e:
            self.logger.error("Template validation failed: %s" % str(e))
            return False

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        if item.type == "maya.session":
            # Maya FBX 내보내기
            return self._maya_export_fbx(settings, item)
        else:
            # Unreal 에셋 내보내기
            return self._unreal_export_fbx(settings, item)

    def _maya_export_fbx(self, settings, item):
        """
        Maya에서 FBX 파일로 내보내기
        """
        # 출력 경로 설정
        publish_path = self._get_publish_path(settings, item)
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # FBX 내보내기 옵션 설정
        mel.eval('FBXResetExport')
        mel.eval('FBXExportFileVersion -v FBX201800')
        mel.eval('FBXExportUpAxis -v y')
        mel.eval('FBXExportShapes -v true')
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportSmoothMesh -v true')
        mel.eval('FBXExportTangents -v true')
        mel.eval('FBXExportInstances -v true')
        mel.eval('FBXExportQuaternion -v euler')
        mel.eval('FBXExportAnimation -v false')
        mel.eval('FBXExportReferencedAssetsContent -v false')
        mel.eval('FBXExportConstraints -v false')
        mel.eval('FBXExportLights -v false')
        mel.eval('FBXExportCameras -v false')
        mel.eval('FBXExportBakeComplexAnimation -v false')

        # FBX 내보내기 실행
        try:
            cmds.FBXExport('-f', publish_path)
        except Exception as e:
            self.logger.error("Failed to export FBX: %s" % str(e))
            return False

        # 퍼블리시 등록
        self._register_publish(settings, item, publish_path)
        return True

    def _unreal_export_fbx(self, settings, item):
        """
        Unreal에서 FBX 파일로 내보내기
        """
        publish_path = self._get_publish_path(settings, item)
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        asset_path = item.properties["asset_path"]
        asset_name = item.properties["asset_name"]

        if _unreal_export_asset_to_fbx(publish_folder, asset_path, asset_name):
            self._register_publish(settings, item, publish_path)
            return True
        return False

    def _get_publish_path(self, settings, item):
        """
        퍼블리시 경로 생성
        """
        publish_template = item.properties["publish_template"]
        fields = {
            "name": item.properties.get("asset_name", ""),
            "Asset": item.context.entity["name"],
            "Step": item.context.step["name"] if item.context.step else "",
            "version": 1,
        }
        return publish_template.apply_fields(fields)

    def _register_publish(self, settings, item, path):
        """
        퍼블리시 등록
        """
        publisher = self.parent
        path = tank.util.ShotgunPath.normalize(path)

        # 퍼블리시 등록
        publish_data = {
            "tk": publisher.sgtk,
            "context": item.context,
            "comment": item.description,
            "path": path,
            "name": os.path.basename(path),
            "created_by": item.get_property("user"),
            "version_number": item.get_property("version_number", 1),
            "thumbnail_path": item.get_thumbnail_as_path(),
            "published_file_type": item.get_property("published_file_type"),
            "dependency_paths": item.get_property("dependency_paths", []),
        }

        # 퍼블리시 실행
        publisher.publish_file(**publish_data)

def _unreal_export_asset_to_fbx(destination_path, asset_path, asset_name):
    """
    Export an asset to FBX from Unreal

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The asset name to use for the FBX filename
    """
    # Create and configure an asset export task
    export_task = _generate_fbx_export_task(destination_path, asset_path, asset_name)

    # Run the export task
    unreal.AssetToolsHelpers.get_asset_tools().export_assets(
        [export_task],
        False  # Don't show the export options dialog
    )

def _generate_fbx_export_task(destination_path, asset_path, asset_name):
    """
    Create and configure an Unreal AssetExportTask

    :param destination_path: The path where the exported FBX will be placed
    :param asset_path: The Unreal asset to export to FBX
    :param asset_name: The FBX filename to export to
    :return the configured AssetExportTask
    """
    # Create an asset export task
    export_task = unreal.AssetExportTask()

    # The asset to export
    export_task.object = unreal.load_asset(asset_path)

    # The name of the file to export to
    export_task.filename = os.path.join(destination_path, "%s.fbx" % asset_name)

    # Replace the file if it exists
    export_task.replace_identical = True

    # Don't auto save the export task settings
    export_task.automated = True

    # Don't show the export options dialog
    export_task.prompt = False

    return export_task
