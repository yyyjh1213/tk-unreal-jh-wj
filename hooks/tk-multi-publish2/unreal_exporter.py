# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk
import unreal
from . import base_exporter

class UnrealExporterPlugin(base_exporter.BaseExporterPlugin):
    """
    Unreal Engine용 내보내기 플러그인입니다.
    에셋과 레벨을 내보내는 기능을 제공합니다.
    """

    @property
    def settings(self):
        """Unreal Engine 내보내기 설정을 정의합니다."""
        base_settings = super(UnrealExporterPlugin, self).settings
        unreal_settings = {
            "Asset Options": {
                "type": "dict",
                "values": {
                    "CreateFolders": True,
                    "ReplaceExisting": True,
                    "SaveAfterExport": True
                },
                "default": {},
                "description": "Unreal Engine 에셋 내보내기 옵션입니다."
            }
        }
        base_settings.update(unreal_settings)
        return base_settings

    def validate_export(self, settings, item):
        """
        Unreal Engine 내보내기 설정을 검증합니다.

        :param dict settings: 설정 딕셔너리
        :param item: 검증할 항목
        :returns: 검증 성공 시 True, 실패 시 False
        """
        if not super(UnrealExporterPlugin, self).validate_export(settings, item):
            return False

        # Unreal Engine 검증
        if not unreal.is_editor():
            self.logger.error("Unreal Editor가 실행 중이 아닙니다.")
            return False

        return True

    def export_content(self, settings, item):
        """
        Unreal Engine 콘텐츠를 내보냅니다.

        :param dict settings: 설정 딕셔너리
        :param item: 내보낼 항목
        :returns: 내보낸 콘텐츠의 경로
        """
        # 내보내기 경로 가져오기
        export_path = self._get_save_path(settings, item)
        if not export_path:
            self.logger.error("내보내기 경로를 가져올 수 없습니다.")
            return None

        # 내보내기 폴더 생성
        self._ensure_export_folder(export_path)

        # 에셋 내보내기 옵션 설정
        asset_options = settings.get("Asset Options", {})
        create_folders = asset_options.get("CreateFolders", True)
        replace_existing = asset_options.get("ReplaceExisting", True)
        save_after_export = asset_options.get("SaveAfterExport", True)

        try:
            # 에셋 유형에 따른 내보내기
            if item.properties.get("asset_type") == "StaticMesh":
                self._export_static_mesh(item, export_path, create_folders, replace_existing)
            elif item.properties.get("asset_type") == "SkeletalMesh":
                self._export_skeletal_mesh(item, export_path, create_folders, replace_existing)
            elif item.properties.get("asset_type") == "Animation":
                self._export_animation(item, export_path, create_folders, replace_existing)
            elif item.properties.get("asset_type") == "Level":
                self._export_level(item, export_path, create_folders, replace_existing)

            # 변경 사항 저장
            if save_after_export:
                unreal.EditorAssetLibrary.save_loaded_assets()

            self.logger.info("Unreal Engine 콘텐츠 내보내기 성공: {}".format(export_path))
            return export_path

        except Exception as e:
            self.logger.error("Unreal Engine 콘텐츠 내보내기 실패: {}".format(str(e)))
            return None

    def _export_static_mesh(self, item, path, create_folders, replace_existing):
        """스태틱 메시를 내보냅니다."""
        pass  # Unreal Engine API를 사용한 구현 필요

    def _export_skeletal_mesh(self, item, path, create_folders, replace_existing):
        """스켈레탈 메시를 내보냅니다."""
        pass  # Unreal Engine API를 사용한 구현 필요

    def _export_animation(self, item, path, create_folders, replace_existing):
        """애니메이션을 내보냅니다."""
        pass  # Unreal Engine API를 사용한 구현 필요

    def _export_level(self, item, path, create_folders, replace_existing):
        """레벨을 내보냅니다."""
        pass  # Unreal Engine API를 사용한 구현 필요
