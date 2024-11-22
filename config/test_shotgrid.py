from shotgun_api3 import Shotgun

# Shotgun 연결 설정
sg = Shotgun("https://jhworld.shotgrid.autodesk.com/", 
             script_name="test_window", 
             api_key="zfwntizblh1kn(sDvqlsguihw")

# Task 엔티티의 스키마 정보 확인
task_schema = sg.schema_field_read('Task')

# content 필드의 타입 정보만 출력
if 'content' in task_schema:
    print("\nTask content 필드 정보:")
    print(task_schema['content'])
    print("\ncontent 필드 타입:", task_schema['content']['data_type']['value'])
else:
    print("content 필드를 찾을 수 없습니다.")

# 전체 Task 스키마 정보 출력 (선택사항이지만 참고용으로 유용)
print("\n전체 Task 스키마 정보:")
for field_name, field_info in task_schema.items():
    if field_name == 'content':  # content 필드에 대해서만 자세히 출력
        print(f"\n=== Content 필드 상세 정보 ===")
        print(f"필드명: {field_name}")
        for key, value in field_info.items():
            print(f"{key}: {value}")