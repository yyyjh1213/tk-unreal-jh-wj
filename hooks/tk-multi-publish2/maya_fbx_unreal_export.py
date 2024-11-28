"""
Hook for exporting Maya files as FBX for Unreal Engine.
Handles FBX export settings and texture conversion for Unreal compatibility.
"""
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaFBXUnrealExportPlugin(HookBaseClass):
    """
    Plugin for exporting Maya FBX files optimized for Unreal Engine.
    Handles FBX export settings and texture conversion.
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
            "Convert Textures": {
                "type": "bool",
                "default": True,
                "description": "Convert procedural textures to file textures before export.",
            },
            "Scale Factor": {
                "type": "float",
                "default": 1.0,
                "description": "Scale factor for the exported FBX.",
            }
        }

    def validate(self, settings, item):
        """
        Validate the scene for export.
        """
        if settings.get("Export Selection", True) and not cmds.ls(selection=True):
            self.logger.warning("Nothing selected for export.")
            return False

        # Check for unsupported texture nodes
        if settings.get("Convert Textures", True):
            unsupported = self._find_unsupported_textures()
            if unsupported:
                self.logger.warning(f"Found unsupported textures: {unsupported}")
                return False

        return True

    def export_fbx(self, settings, item):
        """
        Export the scene or selection as FBX.
        """
        try:
            # Convert textures if needed
            if settings.get("Convert Textures", True):
                self._convert_procedural_textures()

            # Get export path
            path = item.properties["path"]
            
            # Prepare FBX export options
            mel.eval('FBXResetExport')
            
            # Set FBX export settings
            mel.eval('FBXExportFileVersion -v "{}"'.format(settings.get("FBX Version", "FBX201900")))
            mel.eval('FBXExportUpAxis -v "y"')
            mel.eval('FBXExportScaleFactor -v {}'.format(settings.get("Scale Factor", 1.0)))
            mel.eval('FBXExportShapes -v true')
            mel.eval('FBXExportSmoothingGroups -v true')
            mel.eval('FBXExportSkins -v true')
            mel.eval('FBXExportConstraints -v false')
            mel.eval('FBXExportLights -v false')
            mel.eval('FBXExportCameras -v false')
            mel.eval('FBXExportBakeComplexAnimation -v false')
            mel.eval('FBXExportEmbeddedTextures -v true')
            
            # Export selected or all
            if settings.get("Export Selection", True):
                mel.eval('FBXExport -f "{}" -s'.format(path.replace("\\", "/")))
            else:
                mel.eval('FBXExport -f "{}"'.format(path.replace("\\", "/")))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export FBX: {str(e)}")
            return False

    def _find_unsupported_textures(self):
        """
        Find texture nodes that are not supported for FBX export.
        """
        unsupported_types = ['checker', 'ramp']
        unsupported = []
        
        for node_type in unsupported_types:
            nodes = cmds.ls(type=node_type) or []
            unsupported.extend(nodes)
            
        return unsupported

    def _convert_procedural_textures(self):
        """
        Convert procedural textures to file textures using Maya's native functionality.
        """
        # Get all materials in the scene
        materials = cmds.ls(mat=True)
        
        for material in materials:
            # Get all textures connected to the material
            textures = cmds.listConnections(material, type='checker') or []
            
            for texture in textures:
                try:
                    # Get the texture's output connections
                    connections = cmds.listConnections(texture, plugs=True, connections=True, destination=True) or []
                    
                    if connections:
                        # Get the checker pattern colors
                        color1 = cmds.getAttr(f'{texture}.color1')[0]
                        color2 = cmds.getAttr(f'{texture}.color2')[0]
                        
                        # Create a new ramp node instead
                        ramp_node = cmds.shadingNode('ramp', asTexture=True)
                        place2d = cmds.shadingNode('place2dTexture', asUtility=True)
                        
                        # Set up the ramp to look like a checker
                        cmds.setAttr(f'{ramp_node}.type', 3)  # Checker type
                        cmds.setAttr(f'{ramp_node}.interpolation', 0)  # No interpolation
                        
                        # Set colors
                        cmds.setAttr(f'{ramp_node}.colorEntryList[0].color', *color1)
                        cmds.setAttr(f'{ramp_node}.colorEntryList[1].color', *color2)
                        
                        # Connect place2dTexture to ramp node
                        cmds.connectAttr(f'{place2d}.outUV', f'{ramp_node}.uv')
                        cmds.connectAttr(f'{place2d}.outUvFilterSize', f'{ramp_node}.uvFilterSize')
                        
                        # Connect to original destinations
                        for i in range(0, len(connections), 2):
                            src = connections[i]
                            dst = connections[i+1]
                            cmds.connectAttr(f'{ramp_node}.outColor', dst, force=True)
                        
                        # Delete the original checker node
                        cmds.delete(texture)
                        
                        self.logger.info(f"Converted checker {texture} to ramp texture")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to convert texture {texture}: {str(e)}")
                    continue
