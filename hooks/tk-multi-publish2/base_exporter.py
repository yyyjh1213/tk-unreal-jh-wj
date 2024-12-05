# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class BaseExporterPlugin(HookBaseClass):
    """
    기본 내보내기 플러그인 클래스입니다.
    모든 DCC 도구별 exporter의 기본 클래스로 사용됩니다.
    """

    @property
    def settings(self):
        """
        내보내기 설정을 정의합니다.
        """
        return {
            "Export Path Template": {
                "type": "template",
                "default": None,
                "description": "내보내기 경로 템플릿입니다. templates.yml에 정의된 템플릿과 일치해야 합니다."
            },
            "Export Types": {
                "type": "list",
                "values": {
                    "Meshes": True,
                    "Skeletons": True,
                    "Animations": True
                },
                "default": ["Meshes"],
                "description": "내보낼 콘텐츠 유형입니다."
            }
        }

    def validate_export(self, settings, item):
        """
        내보내기 설정을 검증합니다.
        하위 클래스에서 구현해야 합니다.

        :param dict settings: 설정 딕셔너리
        :param item: 검증할 항목
        :returns: 검증 성공 시 True, 실패 시 False
        """
        # 기본 검증
        if not item:
            self.logger.error("내보낼 항목이 없습니다.")
            return False

        if not settings:
            self.logger.error("내보내기 설정이 없습니다.")
            return False

        # 경로 템플릿 검증
        template = settings.get("Export Path Template")
        if not template:
            self.logger.error("내보내기 경로 템플릿이 설정되지 않았습니다.")
            return False

        return True

    def export_content(self, settings, item):
        """
        콘텐츠를 내보냅니다.
        하위 클래스에서 구현해야 합니다.

        :param dict settings: 설정 딕셔너리
        :param item: 내보낼 항목
        :returns: 내보낸 콘텐츠의 경로
        """
        raise NotImplementedError

    def _get_save_path(self, settings, item):
        """
        항목과 설정을 기반으로 저장 경로를 가져옵니다.

        :param dict settings: 설정 딕셔너리
        :param item: 저장 경로를 결정할 항목
        :returns: 항목 저장 경로
        """
        template = settings.get("Export Path Template")
        if not template:
            return None

        # 작업 필드 가져오기
        work_fields = {}
        if item.properties.get("work_template"):
            work_fields = item.properties["work_template"].get_fields(item.properties["path"])

        # 내보내기 경로 생성
        fields = work_fields.copy()
        export_path = template.apply_fields(fields)

        # 경로 정규화
        if export_path:
            export_path = os.path.normpath(export_path)

        return export_path

    def _ensure_export_folder(self, path):
        """
        내보내기 폴더가 존재하는지 확인하고 없으면 생성합니다.

        :param path: 확인할 경로
        """
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
