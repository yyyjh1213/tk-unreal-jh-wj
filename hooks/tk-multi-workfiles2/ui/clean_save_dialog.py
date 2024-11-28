# Clean Save 대화상자 UI 구현
# 파일 저장 시 clean 옵션을 선택할 수 있는 체크박스를 제공합니다.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

class CleanSaveDialog(QtGui.QDialog):
    """
    Clean Save 옵션을 위한 대화상자
    파일 저장 시 clean 모드로 저장할지 선택할 수 있는 체크박스를 제공합니다.
    """
    
    def __init__(self, parent=None):
        super(CleanSaveDialog, self).__init__(parent)
        
        # 대화상자 기본 설정
        self.setWindowTitle("Save Options")
        self.setModal(True)
        
        # 메인 레이아웃 생성
        layout = QtGui.QVBoxLayout(self)
        
        # Clean 저장 옵션 체크박스 추가
        self.clean_checkbox = QtGui.QCheckBox("Save as Clean", self)
        self.clean_checkbox.setToolTip("Save file in clean folder with .clean in filename")
        layout.addWidget(self.clean_checkbox)
        
        # 확인/취소 버튼 추가
        button_layout = QtGui.QHBoxLayout()
        self.ok_button = QtGui.QPushButton("OK", self)
        self.cancel_button = QtGui.QPushButton("Cancel", self)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 버튼 클릭 시그널 연결
        self.ok_button.clicked.connect(self.accept)  # 확인 버튼 클릭 시 대화상자 승인
        self.cancel_button.clicked.connect(self.reject)  # 취소 버튼 클릭 시 대화상자 거부
        
    def is_clean_enabled(self):
        """
        Clean 저장 옵션의 선택 여부를 반환
        
        :returns: Boolean - Clean 체크박스가 선택되었는지 여부
        """
        return self.clean_checkbox.isChecked()
