# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaSessionCollector(HookBaseClass):
    """
    Collector that operates on the maya session. Should inherit from the basic
    collector hook.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        # get the current maya scene path
        scene_path = cmds.file(query=True, sn=True)
        
        if not scene_path:
            self.logger.warning("현재 Maya 씬이 저장되지 않았습니다. 먼저 저장해주세요!")
            return

        # ensure the scene path is normalized
        scene_path = sgtk.util.ShotgunPath.normalize(scene_path)

        # create the session item for the maya scene
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            os.path.basename(scene_path)
        )

        # get session path and name
        session_item.properties["path"] = scene_path
        session_item.properties["file_info"] = self._get_file_info(scene_path)

        self.logger.info("Maya 씬 수집됨: %s" % scene_path)

        # look for meshes in the scene
        meshes = cmds.ls(type="mesh", long=True, noIntermediate=True)
        if meshes:
            mesh_item = session_item.create_item(
                "maya.fbx",
                "Maya FBX",
                "All Meshes"
            )
            mesh_item.properties["meshes"] = meshes
            self.logger.info("메시 %d개 발견됨" % len(meshes))
            
            # Add a display name to show in the UI
            mesh_item.properties["publish_name"] = "Maya Meshes as FBX"
            
            # Add the maya session file to the mesh item
            mesh_item.properties["maya_path"] = scene_path
            
            # Set the icon for the item
            mesh_item.set_icon_from_path(":/icons/alembic.png")
            
            # Enable this item by default
            mesh_item.checked = True
        else:
            self.logger.warning("씬에서 메시를 찾을 수 없습니다!")

    def _get_file_info(self, path):
        """
        Return file info for the given path
        """
        return {
            "path": path,
            "filename": os.path.basename(path),
            "extension": os.path.splitext(path)[1],
            "size": os.path.getsize(path),
        }
