# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import maya.cmds as cmds
import sgtk
from .base_hooks.publish_plugin import PublishPlugin

class MayaFBXPublishPlugin(PublishPlugin):
    """
    Plugin for publishing an FBX file from Maya for use in Unreal Engine.
    """

    @property
    def name(self):
        """
        One line display name describing the plugin
        """
        return "Publish Maya FBX"

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
        """
        return {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published FBX files. Should "
                             "correspond to a template defined in templates.yml.",
            }
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["maya.fbx"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.
        """
        if "meshes" not in item.properties:
            self.logger.warning("메시 정보를 찾을 수 없습니다!")
            return {"accepted": False}

        if not item.properties["meshes"]:
            self.logger.warning("씬에 메시가 없습니다!")
            return {"accepted": False}

        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        path = self._get_publish_path(settings, item)
        
        if not path:
            self.logger.error("퍼블리시 경로를 생성할 수 없습니다!")
            return False

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent
        engine = sgtk.platform.current_engine()

        # Get the publish path
        publish_path = self._get_publish_path(settings, item)

        # Ensure the publish folder exists
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        try:
            # Export the FBX file
            self._export_fbx(item.properties["meshes"], publish_path)
            self.logger.info("FBX 파일이 성공적으로 내보내졌습니다: %s" % publish_path)
        except Exception as e:
            self.logger.error("FBX 파일 내보내기 실패: %s" % e)
            return False

        return True

    def finalize(self, settings, item):
        """
        Execute the finalization pass.
        """
        pass

    def _get_publish_path(self, settings, item):
        """
        Get the publish path for the FBX file.
        """
        publisher = self.parent

        # Get the template path from the settings
        template_name = settings["Publish Template"].value
        if not template_name:
            self.logger.error("퍼블리시 템플릿이 설정되지 않았습니다!")
            return None

        # Get template from the engine
        template = publisher.get_template_by_name(template_name)
        if not template:
            self.logger.error("템플릿을 찾을 수 없습니다: %s" % template_name)
            return None

        # Get fields from the context
        fields = item.context.as_template_fields(template)
        
        # Get additional fields from item properties
        fields["name"] = item.properties.get("publish_name", "")
        fields["version"] = publisher.util.get_next_version_number(item.context, template, fields)

        # Apply fields to template to get publish path
        return template.apply_fields(fields)

    def _export_fbx(self, meshes, path):
        """
        Export the meshes as an FBX file.
        """
        # Select the meshes for export
        cmds.select(meshes, replace=True)

        # Set up FBX export options
        kwargs = {
            "file": path,
            "force": True,
            "options": True,
            "type": "FBX export",
            "preserveReferences": True,
            "shader": True,
            "smoothing": True,
            "triangulate": True
        }

        # Export the file
        cmds.file(**kwargs)
