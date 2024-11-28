"""
Hook for exporting Maya files as FBX for Unreal Engine.
"""
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXUnrealExportPlugin(HookBaseClass):
    """
    Plugin for publishing Maya FBX files optimized for Unreal Engine.
    """

    @property
    def name(self):
        """The name of this plugin."""
        return "Maya FBX Unreal Export"

    @property
    def description(self):
        """The description of this plugin."""
        return "Export Maya scene as FBX file optimized for Unreal Engine."

    @property
    def settings(self):
        """The plugin settings."""
        return {
            "Export Selection": {
                "type": "bool",
                "default": True,
                "description": "Export only selected objects if enabled.",
            },
            "FBX Version": {
                "type": "str",
                "default": "FBX201900",
                "description": "FBX file version to use.",
            },
        }

    def validate(self, settings, item):
        """
        Validate the item before export.
        """
        if not cmds.ls(selection=True) and settings["Export Selection"]:
            self.logger.warning("Nothing selected for export.")
            return False
        return True

    def export_fbx(self, settings, item):
        """
        Export the Maya scene as FBX with Unreal-optimized settings.
        """
        # Get the path
        path = item.properties.get("path", "")
        if not path:
            self.logger.error("No output path set.")
            return None

        # Ensure the output folder exists
        output_folder = os.path.dirname(path)
        self.parent.ensure_folder_exists(output_folder)

        # Get export selection mode
        export_selection = settings["Export Selection"].value

        # Prepare FBX export options
        mel.eval('FBXResetExport')
        
        # Set up axis conversion and scale
        mel.eval('FBXExportUpAxis y')
        mel.eval('FBXExportScaleFactor 1')
        mel.eval('FBXExportConvertUnitString cm')  # Add unit conversion
        mel.eval('FBXExportAxisConversionMethod none')  # Prevent axis conversion issues
        
        # Configure FBX version
        mel.eval(f'FBXExportFileVersion {settings["FBX Version"].value}')
        
        # Configure geometry export options
        mel.eval('FBXExportSmoothingGroups -v 1')
        mel.eval('FBXExportHardEdges -v 0')
        mel.eval('FBXExportTangents -v 1')
        mel.eval('FBXExportSmoothMesh -v 1')
        mel.eval('FBXExportInstances -v 0')
        mel.eval('FBXExportTriangulate -v 1')
        mel.eval('FBXExportQuaternion -v euler')  # Add quaternion export mode
        mel.eval('FBXExportShapes -v 1')  # Export blend shapes
        mel.eval('FBXExportSkins -v 1')  # Export skin deformations
        
        # Configure animation and deformation options
        mel.eval('FBXExportAnimationOnly -v 0')
        mel.eval('FBXExportBakeComplexAnimation -v 1')
        mel.eval('FBXExportBakeComplexStart -v 0')
        mel.eval('FBXExportBakeComplexEnd -v 100')
        mel.eval('FBXExportBakeComplexStep -v 1')
        mel.eval('FBXExportReferencedAssetsContent -v 1')  # Include referenced assets
        mel.eval('FBXExportInputConnections -v 1')  # Export input connections
        
        # Configure includes
        mel.eval('FBXExportInAscii -v 1')  # Change to ASCII format for better compatibility
        mel.eval('FBXExportLights -v 0')  # Disable lights export
        mel.eval('FBXExportCameras -v 0')  # Disable cameras export
        mel.eval('FBXExportConstraints -v 1')
        mel.eval('FBXExportSkeletonDefinitions -v 1')
        
        # Configure materials and textures
        mel.eval('FBXExportMaterials -v 1')
        mel.eval('FBXExportTextures -v 1')
        mel.eval('FBXExportEmbeddedTextures -v 0')
        
        try:
            # Perform the export
            if export_selection:
                mel.eval(f'FBXExport -f "{path}" -s')
            else:
                mel.eval(f'FBXExport -f "{path}"')
            
            self.logger.info(f"FBX exported successfully to: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export FBX: {str(e)}")
            return False

    def execute(self, settings, item):
        """
        Execute the plugin.
        """
        # Validate the export
        if not self.validate(settings, item):
            return False
            
        # Perform the export
        result = self.export_fbx(settings, item)
        
        if not result:
            self.logger.error("Failed to export FBX file.")
            return False
            
        self.logger.info("FBX Export completed successfully.")
        return True
