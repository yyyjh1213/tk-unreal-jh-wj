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
            
        # Convert procedural textures to file textures
        self._convert_procedural_textures()
        return True
        
    def _convert_procedural_textures(self):
        """
        Convert procedural textures to file textures.
        """
        # Get all materials in the scene
        materials = cmds.ls(mat=True)
        
        for material in materials:
            # Get all textures connected to the material
            textures = cmds.listConnections(material, type='texture2d') or []
            textures.extend(cmds.listConnections(material, type='place2dTexture') or [])
            textures.extend(cmds.listConnections(material, type='checker') or [])
            
            for texture in textures:
                # Skip if it's already a file texture
                if cmds.nodeType(texture) == 'file':
                    continue
                    
                try:
                    # Get the texture's output connections
                    connections = cmds.listConnections(texture, plugs=True, connections=True, destination=True) or []
                    
                    if connections:
                        # Create a new file texture node
                        file_node = cmds.shadingNode('file', asTexture=True)
                        place2d = cmds.shadingNode('place2dTexture', asUtility=True)
                        
                        # Connect place2dTexture to file node
                        cmds.connectAttr(f'{place2d}.coverage', f'{file_node}.coverage')
                        cmds.connectAttr(f'{place2d}.translateFrame', f'{file_node}.translateFrame')
                        cmds.connectAttr(f'{place2d}.rotateFrame', f'{file_node}.rotateFrame')
                        cmds.connectAttr(f'{place2d}.mirrorU', f'{file_node}.mirrorU')
                        cmds.connectAttr(f'{place2d}.mirrorV', f'{file_node}.mirrorV')
                        cmds.connectAttr(f'{place2d}.stagger', f'{file_node}.stagger')
                        cmds.connectAttr(f'{place2d}.wrapU', f'{file_node}.wrapU')
                        cmds.connectAttr(f'{place2d}.wrapV', f'{file_node}.wrapV')
                        cmds.connectAttr(f'{place2d}.repeatUV', f'{file_node}.repeatUV')
                        cmds.connectAttr(f'{place2d}.offset', f'{file_node}.offset')
                        cmds.connectAttr(f'{place2d}.rotateUV', f'{file_node}.rotateUV')
                        cmds.connectAttr(f'{place2d}.noiseUV', f'{file_node}.noiseUV')
                        cmds.connectAttr(f'{place2d}.vertexUvOne', f'{file_node}.vertexUvOne')
                        cmds.connectAttr(f'{place2d}.vertexUvTwo', f'{file_node}.vertexUvTwo')
                        cmds.connectAttr(f'{place2d}.vertexUvThree', f'{file_node}.vertexUvThree')
                        cmds.connectAttr(f'{place2d}.vertexCameraOne', f'{file_node}.vertexCameraOne')
                        
                        # Connect to original destinations
                        for i in range(0, len(connections), 2):
                            src = connections[i]
                            dst = connections[i+1]
                            cmds.connectAttr(f'{file_node}.outColor', dst, force=True)
                        
                        # Set a default texture if it's a checker
                        if cmds.nodeType(texture) == 'checker':
                            # Create a temporary checker texture file
                            import tempfile
                            import os
                            
                            temp_dir = tempfile.gettempdir()
                            texture_path = os.path.join(temp_dir, f'temp_checker_{texture}.png')
                            
                            # Create a default checker pattern
                            from PIL import Image
                            img = Image.new('RGB', (256, 256), color='white')
                            pixels = img.load()
                            
                            # Create checker pattern
                            for i in range(img.size[0]):
                                for j in range(img.size[1]):
                                    if (i // 32 + j // 32) % 2:
                                        pixels[i,j] = (128, 128, 128)
                            
                            img.save(texture_path)
                            
                            # Assign the texture file
                            cmds.setAttr(f'{file_node}.fileTextureName', texture_path, type="string")
                        
                        self.logger.info(f"Converted {texture} to file texture")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to convert texture {texture}: {str(e)}")
                    continue

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
