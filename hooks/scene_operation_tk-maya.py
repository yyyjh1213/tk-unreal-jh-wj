"""
Hook for performing operations with maya.
"""
import maya.cmds as cmds
import maya.mel as mel
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class SceneOperation(HookBaseClass):
    """
    Hook called to perform an operation with the
    current scene
    """
    
    def _export_clean_fbx(self, file_path):
        """
        Clean 모드로 FBX 파일을 내보내는 헬퍼 함수
        
        :param file_path: 원본 저장 경로
        :return: 실제 저장된 FBX 파일 경로
        """
        # clean 저장을 위한 새로운 폴더 경로 생성
        folder = os.path.dirname(file_path)
        clean_folder = os.path.join(folder, "clean")
        self.parent.ensure_folder_exists(clean_folder)
        
        # 파일명에 .clean 추가하고 버전 정보 유지
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        if ".v" in name:
            # 버전 번호가 있는 경우 처리
            base_name = name.split(".v")[0]
            version = name.split(".v")[1]
            clean_name = f"{base_name}.clean.v{version}.fbx"
        else:
            # 버전 번호가 없는 경우 처리
            clean_name = f"{name}.clean.fbx"
        
        # clean 폴더에 FBX로 내보내기
        clean_path = os.path.join(clean_folder, clean_name)
        
        # FBX 내보내기 옵션 설정
        mel.eval('FBXResetExport')  # FBX 내보내기 옵션 초기화
        
        # FBX 내보내기 기본 설정
        mel.eval('FBXExportFileVersion -v FBX201800')  # FBX 2018 버전
        mel.eval('FBXExportInputConnections -v 0')
        mel.eval('FBXExportIncludeChildren -v 1')
        mel.eval('FBXExportInAscii -v 1')  # ASCII 형식으로 내보내기
        
        # 애니메이션 설정
        mel.eval('FBXExportAnimationOnly -v 0')
        mel.eval('FBXExportBakeComplexAnimation -v 1')
        mel.eval('FBXExportBakeComplexStart -v 0')
        mel.eval('FBXExportBakeComplexEnd -v 1')
        mel.eval('FBXExportBakeComplexStep -v 1')
        
        # 기하학 설정
        mel.eval('FBXExportSmoothingGroups -v 1')
        mel.eval('FBXExportHardEdges -v 0')
        mel.eval('FBXExportTangents -v 0')
        mel.eval('FBXExportSmoothMesh -v 1')
        mel.eval('FBXExportInstances -v 0')
        
        # 기타 설정
        mel.eval('FBXExportReferencedAssetsContent -v 1')
        mel.eval('FBXExportUseSceneName -v 0')
        
        # FBX 파일로 내보내기
        cmds.file(clean_path, force=True, exportAll=True, type="FBX export")
        
        # 현재 씬도 저장
        cmds.file(save=True, force=True)
        
        return clean_path

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point

        :param operation:       String
                              Scene operation to perform

        :param file_path:       String
                              File path to use if the operation
                              requires it (e.g. open)

        :param context:         Context
                              The context the file operation is being
                              performed in.

        :param parent_action:   This is the action that this scene operation is
                              being executed for.  This can be one of:
                              - open_file
                              - new_file
                              - save_file_as
                              - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                              then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not
        
        :param kwargs:          Additional arguments dictionary that includes:
                              - clean_enabled: Boolean flag indicating if clean save is enabled
        """
        if operation == "current_path":
            # 현재 씬 파일 경로 반환
            return cmds.file(query=True, sceneName=True)
            
        # 모든 파일 작업에서 폴더 존재 확인
        folder = os.path.dirname(file_path)
        self.parent.ensure_folder_exists(folder)

        if operation == "open":
            # 파일 열기
            cmds.file(file_path, open=True, force=True)
            
        elif operation in ["save", "save_as"]:
            # 체크박스에서 clean 옵션이 선택되었는지 확인
            clean_enabled = kwargs.get("clean_enabled", False)
            
            if clean_enabled:
                self._export_clean_fbx(file_path)
            else:
                # 일반 저장
                cmds.file(rename=file_path)
                cmds.file(save=True, force=True)
                
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            while cmds.file(query=True, modified=True):
                # Scene has been modified:
                res = cmds.confirmDialog(title="Save your scene?",
                                       message="Your scene has unsaved changes. Save before proceeding?",
                                       button=["Save", "Don't Save", "Cancel"],
                                       defaultButton="Save",
                                       cancelButton="Cancel",
                                       dismissString="Cancel")

                if res == "Save":
                    scene_name = cmds.file(query=True, sceneName=True)
                    if not scene_name:
                        cmds.SaveSceneAs()
                    else:
                        cmds.file(save=True)
                elif res == "Cancel":
                    return False
                else:
                    break

            # do new file:
            cmds.file(newFile=True, force=True)
            return True
