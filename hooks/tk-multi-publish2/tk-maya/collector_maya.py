"""
Collector for Maya that finds various publishable items in the current session.
"""
import sgtk
import maya.cmds as cmds

HookBaseClass = sgtk.get_hook_baseclass()

class MayaCollector(HookBaseClass):
    """
    Collector that operates on the current Maya session.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session and creates publishable items for the
        scene and any assets contained within it.
        """
        
        # Create an item representing the current maya session
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            cmds.file(query=True, sceneName=True)
        )
        
        # Get the icon path to display for this item
        icon_path = self._get_icon_path("maya")
        session_item.set_icon_from_path(icon_path)
        
        # Look for meshes in the scene
        meshes = cmds.ls(type="mesh", long=True)
        
        if meshes:
            # Create a single item for all meshes
            mesh_item = parent_item.create_item(
                "maya.fbx",
                "Maya Meshes",
                "All Maya Meshes"
            )
            
            # Add the list of meshes to the properties
            mesh_item.properties["meshes"] = meshes
            
        return True

    def _get_icon_path(self, icon_name):
        """
        Return the full path to the given icon.
        """
        # Look for the icon in the hooks/icons directory
        return "path/to/icons/%s.png" % icon_name
