"""
Hook for publishing the current Maya session.
"""
import os
import sgtk
import maya.cmds as cmds
from ...common.base_publisher import BasePublisher

class MayaSessionPublisher(BasePublisher):
    @property
    def publish_file_type(self):
        return "Maya Scene"
        
    def _do_publish(self, settings, item, publish_path):
        """
        Save the current Maya session to the publish path.
        """
        try:
            # Save the current scene
            cmds.file(rename=publish_path)
            cmds.file(save=True, type='mayaAscii')
            return True
        except Exception as e:
            self.logger.error(f"Failed to save Maya session: {str(e)}")
            return False
