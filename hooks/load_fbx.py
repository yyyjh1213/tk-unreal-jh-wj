"""
Hook for loading FBX files into Unreal Engine.
"""
import os
import unreal
import sgtk

class UnrealFBXLoader(sgtk.Hook):
    def execute(self, path, **kwargs):
        """
        Load an FBX file into Unreal Engine.
        
        :param path: Path to the FBX file to load
        :param kwargs: Additional arguments
        :returns: True if successful, False otherwise
        """
        try:
            # 경로 정규화
            fbx_path = os.path.normpath(path)
            
            # 임포트 작업을 위한 task 생성
            import_task = unreal.AssetImportTask()
            import_task.set_editor_property('automated', True)
            import_task.set_editor_property('destination_name', '')
            import_task.set_editor_property('destination_path', '/Game/Assets')
            import_task.set_editor_property('filename', fbx_path)
            import_task.set_editor_property('replace_existing', True)
            import_task.set_editor_property('save', True)
            
            # FBX 임포트 옵션 설정
            fbx_import_options = unreal.FbxImportUI()
            fbx_import_options.set_editor_property('import_mesh', True)
            fbx_import_options.set_editor_property('import_textures', True)
            fbx_import_options.set_editor_property('import_materials', True)
            fbx_import_options.set_editor_property('import_as_skeletal', False)  # 스태틱 메시로 임포트
            
            # 스켈레탈 메시 옵션
            fbx_import_options.skeletal_mesh_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
            fbx_import_options.skeletal_mesh_import_data.set_editor_property('import_rotation', unreal.Rotator(0.0, 0.0, 0.0))
            fbx_import_options.skeletal_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)
            
            # 스태틱 메시 옵션
            fbx_import_options.static_mesh_import_data.set_editor_property('import_translation', unreal.Vector(0.0, 0.0, 0.0))
            fbx_import_options.static_mesh_import_data.set_editor_property('import_rotation', unreal.Rotator(0.0, 0.0, 0.0))
            fbx_import_options.static_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)
            fbx_import_options.static_mesh_import_data.set_editor_property('combine_meshes', True)
            fbx_import_options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', True)
            fbx_import_options.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
            
            # 임포트 옵션 설정
            import_task.set_editor_property('options', fbx_import_options)
            
            # 임포트 실행
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])
            
            self.parent.logger.info(f"Successfully imported FBX: {fbx_path}")
            return True
            
        except Exception as e:
            self.parent.logger.error(f"Failed to import FBX: {str(e)}")
            return False
