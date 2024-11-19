from shotgun_api3 import Shotgun

sg = Shotgun("https://jhworld.shotgrid.autodesk.com/", 
script_name="test_window", 
api_key="zfwntizblh1kn(sDvqlsguihw") 

#프로젝트 확인
projects = sg.find("Project", [], ["name"])
print(f"프로젝트 목록 : {projects}")

#애셋 불러오기 설정
#asset_load_config = sg.find("Asset", [], ["code", "project"])
#print(f"애셋 불러오기 설정 목록 : {asset_load_config}") 

#파이프라인 설정 확인
#config = sg.find("PipelineConfiguration", [], ["code", "project"])
#print(f"파이프라인 설정 목록 : {config}")

#새 파이프라인 설정 생성
pipeline_config_data = {
    "project": {"type": "Project", "id": 122},
    "code": "Remote_unreal_jh2",
    "users": "junghyun Yeom",
    "windows_path": r"c:\shotgrid_config\tk-config-unreal_ww",
    "linux_path": "/shotgrid_config/tk-config-unreal_ww",
    "mac_path": "/shotgrid_config/tk-config-unreal_ww",
    "plugin_ids": "UE",
    "descriptor": "sgtk:descriptor:dev?path=C:/shotgrid_config/tk-config-unreal_ww"
}

try:
    result = sg.create("PipelineConfiguration", pipeline_config_data)
    print("Created Pipeline Configuration:", result)
except Exception as e:
    print("Error creating pipeline configuration:", str(e))

storage_list = sg.find("LocalStorage", [], ["code", "id"])

for storage in storage_list:
    print(f"Storage Name: {storage['code']}, ID: {storage['id']}")

# Project entity type 스키마 확인
project_schema = sg.schema_field_read('Project')
print("\nProject 엔티티 스키마:")
for field_name, field_info in project_schema.items():
    print(f"필드명: {field_name}")
    print(f"필드 정보: {field_info}")
    print("---")

# 특정 프로젝트의 모든 필드 데이터 확인
project_fields = sg.find_one('Project', 
                           [['id', 'is', 122]], # 프로젝트 ID 122 기준
                           list(project_schema.keys()))
print("\n프로젝트 상세 정보:")
for field, value in project_fields.items():
    print(f"{field}: {value}")