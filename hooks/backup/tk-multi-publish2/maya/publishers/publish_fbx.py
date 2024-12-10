"""
Hook for publishing FBX files from Maya for use in Unreal Engine.
"""
import sgtk
import maya.cmds as cmds
import maya.mel as mel
import os
from ...common.base_publisher import BasePublisher

class MayaFBXPublisher(BasePublisher):
    @property
    def publish_file_type(self):
        return "FBX"
        
    def _do_publish(self, settings, item, publish_path):
        """
        Export selected meshes to FBX format.
        """
        # Get meshes to export
        meshes = item.properties.get("meshes", [])
        if not meshes:
            self.logger.error("No meshes found to export")
            return False
            
        # Setup FBX export options
        mel.eval('FBXExportFileVersion -v FBX201800')
        mel.eval('FBXExportUpAxis -v y')
        mel.eval('FBXExportScaleFactor -v 1.0')
        
        try:
            # Select meshes and export
            cmds.select(meshes, replace=True)
            cmds.file(publish_path, 
                     force=True, 
                     options="v=0;", 
                     type="FBX export", 
                     preserveReferences=True, 
                     exportSelected=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to export FBX: {str(e)}")
            return False
