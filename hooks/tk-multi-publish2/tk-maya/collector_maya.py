"""
Maya collector that finds publishable items in the current session.
"""
import maya.cmds as cmds
from ..common.base_collector import BaseCollector

class MayaCollector(BaseCollector):
    """
    Collector for Maya that finds various publishable items in the current session.
    """
    
    @property
    def session_icon_name(self):
        return "maya"
    
    def _create_session_item(self, parent_item):
        """
        Create a session item representing the current Maya session.
        """
        return parent_item.create_item(
            "maya.session",
            "Maya Session",
            cmds.file(query=True, sceneName=True)
        )
    
    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session and creates publishable items.
        """
        # Get the base session item
        session_item = super().process_current_session(settings, parent_item)
        
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
