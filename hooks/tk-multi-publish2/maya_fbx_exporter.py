# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXExporter(HookBaseClass):
    """
    Hook for exporting FBX files from Maya for Unreal Engine.
    """

    def export_fbx(self, settings, item):
        """
        Export the Maya scene as an FBX file.

        :param dict settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: Path to the exported FBX file
        """
        publisher = self.parent
        
        # get the path to export the fbx to
        work_template = item.properties["work_template"]
        work_fields = work_template.get_fields(item.properties["path"])
        
        # ensure the export folder exists
        export_folder = os.path.dirname(item.properties["path"])
        self.parent.ensure_folder_exists(export_folder)
        
        # set the fbx export options
        mel.eval('FBXResetExport')
        
        if cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            mel.eval('FBXExportFileVersion -v FBX201800')
            mel.eval('FBXExportUpAxis -v y')
            mel.eval('FBXExportShapes -v true')
            mel.eval('FBXExportSkins -v true')
            mel.eval('FBXExportAnimationOnly -v false')
            mel.eval('FBXExportBakeComplexAnimation -v true')
            mel.eval('FBXExportUseSceneName -v false')
            mel.eval('FBXExportQuaternion -v euler')
            mel.eval('FBXExportCameras -v false')
            mel.eval('FBXExportLights -v false')
            
            # export the fbx file
            fbx_path = item.properties["path"]
            mel.eval('FBXExport -f "%s" -s' % fbx_path.replace('\\', '/'))
            
            self.logger.debug(
                "FBX export successful. FBX file written to: %s" % fbx_path
            )
            
            return fbx_path
            
        else:
            self.logger.error("FBX plugin not loaded. Unable to export FBX file.")
            return None
