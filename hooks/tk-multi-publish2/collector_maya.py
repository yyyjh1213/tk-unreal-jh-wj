"""
This hook collects items to be published from Maya for Unreal Engine.
"""
import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaUnrealSessionCollector(HookBaseClass):
    """
    Collector that operates on the current Maya session.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current Maya session and creates publish items for FBX export.
        """
        # Get the current Maya scene path
        scene_path = cmds.file(query=True, sn=True)
        if not scene_path:
            self.logger.warning("Current Maya scene is not saved.")
            return

        # Create the FBX export item
        fbx_item = parent_item.create_item(
            "maya.fbx.unreal",
            "Unreal FBX Export",
            "FBX Export for Unreal"
        )

        # Set the FBX output path
        fbx_path = scene_path.replace(".ma", ".fbx").replace(".mb", ".fbx")
        fbx_item.properties["path"] = fbx_path

        # Set the icon
        fbx_item.set_icon_from_path(":/icons/alembic.png")

        # Add the description
        fbx_item.description = "FBX file optimized for Unreal Engine export."

        self.logger.info("Collected FBX export item for Unreal Engine.")
