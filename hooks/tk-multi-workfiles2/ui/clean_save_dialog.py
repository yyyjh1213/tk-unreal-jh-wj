import sgtk
import os
from sgtk.platform.qt import QtCore, QtGui

class CleanSaveDialog(QtGui.QDialog):
    """
    Clean Save 옵션을 위한 대화상자
    파일 저장 시 clean 모드로 저장할지 선택할 수 있는 체크박스를 제공합니다.
    체크박스 선택 시 자동으로 clean 디렉토리를 생성합니다.
    """
    
    def __init__(self, parent=None):
        super(CleanSaveDialog, self).__init__(parent)
        
        # Shotgun Toolkit 엔진 가져오기
        self._app = sgtk.platform.current_bundle()
        
        # 대화상자 기본 설정
        self.setWindowTitle("Save Options")
        self.setModal(True)
        
        # 메인 레이아웃 생성
        layout = QtGui.QVBoxLayout(self)
        
        # Clean 저장 옵션 체크박스 추가
        self.clean_checkbox = QtGui.QCheckBox("Save as Clean", self)
        self.clean_checkbox.setToolTip("Save file in clean folder with .clean in filename")
        self.clean_checkbox.stateChanged.connect(self._on_clean_state_changed)
        layout.addWidget(self.clean_checkbox)
        
        # 확인/취소 버튼 추가
        button_layout = QtGui.QHBoxLayout()
        self.ok_button = QtGui.QPushButton("OK", self)
        self.cancel_button = QtGui.QPushButton("Cancel", self)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 버튼 클릭 시그널 연결
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def _on_clean_state_changed(self, state):
        """
        Clean 체크박스 상태가 변경될 때 호출되는 메서드
        체크박스가 선택되면 clean 디렉토리를 생성합니다.
        
        :param state: 체크박스의 현재 상태
        """
        if state == QtCore.Qt.Checked:
            try:
                # 현재 컨텍스트 가져오기
                context = self._app.context
                
                # 현재 DCC 엔진 이름 가져오기 (예: tk-maya)
                engine_name = self._app.engine.name.replace("tk-", "")
                
                # 에셋 또는 샷 경로 결정
                if context.entity["type"] == "Asset":
                    template = self._app.sgtk.templates["maya_asset_clean_work"]
                else:
                    template = self._app.sgtk.templates["maya_shot_clean_work"]
                
                # 템플릿에서 clean 디렉토리 경로 추출
                fields = context.as_template_fields(template)
                clean_dir = template.apply_fields(fields)
                clean_dir = os.path.dirname(clean_dir)  # 파일명 제거하고 디렉토리 경로만 가져오기
                
                # clean 디렉토리가 없으면 생성
                if not os.path.exists(clean_dir):
                    os.makedirs(clean_dir)
                    self._app.log_debug("Created clean directory: %s" % clean_dir)
                    
            except Exception as e:
                self._app.log_warning("Failed to create clean directory: %s" % str(e))
        
    def is_clean_enabled(self):
        """
        Clean 저장 옵션의 선택 여부를 반환
        
        :returns: Boolean - Clean 체크박스가 선택되었는지 여부
        """
        return self.clean_checkbox.isChecked()
