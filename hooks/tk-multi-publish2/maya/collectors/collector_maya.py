"""
Maya collector for gathering publishable items.
"""
import sgtk
from ...common.base_collector import BaseCollector

class MayaCollector(BaseCollector):
    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current Maya session and creates publishable items.
        """
        engine = self.parent.engine
        
        # Create session item
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            "Current Maya Session"
        )
        
        # Add session properties
        session_item.properties["scene_path"] = cmds.file(query=True, sceneName=True)
        
        return session_item
