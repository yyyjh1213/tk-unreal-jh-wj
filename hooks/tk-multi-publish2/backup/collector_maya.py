"""
이 훅은 Maya에서 Unreal Engine용 퍼블리시 아이템을 수집합니다.
작동 원리:
1. 현재 Maya 씬을 분석하여 FBX 내보내기에 필요한 아이템을 생성
2. 씬 파일의 경로를 기반으로 FBX 출력 경로를 설정
3. 각 아이템에 대한 아이콘과 설명을 설정
"""
import os
import maya.cmds as cmds
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class MayaUnrealSessionCollector(HookBaseClass):
    """
    현재 Maya 세션에서 작동하는 수집기 클래스입니다.
    Unreal Engine으로 내보내기 위한 FBX 파일 생성을 준비합니다.
    """

    def process_current_session(self, settings, parent_item):
        """
        현재 Maya 세션을 분석하고 FBX 내보내기를 위한 퍼블리시 아이템을 생성합니다.
        
        작동 과정:
        1. 현재 Maya 씬의 경로를 확인
        2. 씬이 저장되지 않은 경우 경고 메시지 출력
        3. FBX 내보내기 아이템 생성
        4. 출력 경로를 .ma/.mb 확장자에서 .fbx로 변경
        5. 아이콘 및 설명 설정
        """
        # Get the current Maya scene path
        scene_path = cmds.file(query=True, sn=True)
        if not scene_path:
            self.logger.warning("Current Maya scene is not saved.")
            return

        # Create the FBX export item
        fbx_item = parent_item.create_item(
            "maya.fbx.unreal",
            "Unreal FBX Export",
            "FBX Export for Unreal"
        )

        # Set the FBX output path
        fbx_path = scene_path.replace(".ma", ".fbx").replace(".mb", ".fbx")
        fbx_item.properties["path"] = fbx_path

        # Set the icon
        fbx_item.set_icon_from_path(":/icons/alembic.png")

        # Add the description
        fbx_item.description = "FBX file optimized for Unreal Engine export."

        self.logger.info("Collected FBX export item for Unreal Engine.")
