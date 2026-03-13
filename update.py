import urllib.request
import json
import os
import re

# 🚨 원작자의 깃허브 주소
TARGET_REPO = "diarrhea3/YTLiteDiarrhea"
JSON_FILE = "app.json"

def update_json():
    # 1. 원작자의 최신 릴리즈 정보 가져오기
    url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            release_date = data['published_at']
            release_title = data['name'] # 릴리즈 제목 가져오기 (예: "21.10.2 YouTubePlus v5.2b4")
            
            # ipa 파일 다운로드 링크 찾기
            download_url = ""
            size = 0
            for asset in data['assets']:
                if asset['name'].endswith('.ipa'):
                    download_url = asset['browser_download_url']
                    size = asset['size']
                    break
    except Exception as e:
        print("릴리즈 정보를 가져오는데 실패했습니다:", e)
        return

    if not download_url:
        print("최신 릴리즈에 .ipa 파일이 없습니다.")
        return

    # 🔥 핵심: 릴리즈 제목의 맨 앞에서 버전 숫자만 추출 (예: "21.10.2")
    # 정규표현식으로 맨 앞의 숫자.숫자(.숫자) 형태를 정확히 끄집어냅니다.
    version_match = re.search(r'^v?(\d+\.\d+(?:\.\d+)?)', release_title)
    
    if version_match:
        latest_version = version_match.group(1) # "21.10.2"만 성공적으로 추출
    else:
        # 혹시 제목 형식이 바뀌어 못 찾으면 예비로 태그 이름을 씁니다.
        latest_version = data['tag_name'].lstrip('v') 

    # 2. 내 app.json 읽기
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        apps_data = json.load(f)

    # 3. 버전 비교하기
    current_version = apps_data['apps'][0]['version'].lstrip('v')

    if latest_version != current_version:
        print(f"새로운 버전을 발견했습니다! : {latest_version}")
        # 내 JSON 파일 업데이트
        apps_data['apps'][0]['version'] = latest_version
        apps_data['apps'][0]['versionDate'] = release_date
        apps_data['apps'][0]['downloadURL'] = download_url
        if size > 0:
            apps_data['apps'][0]['size'] = size
        
        # 4. 수정된 내용 저장하기
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, indent=2, ensure_ascii=False)
        print("app.json 업데이트 완료.")
    else:
        print(f"이미 최신 버전입니다. (현재: {current_version})")

if __name__ == "__main__":
    update_json()
