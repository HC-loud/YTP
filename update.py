import urllib.request
import json
import os
import re

# 🚨 여기에 원작자의 깃허브 주소를 넣으세요
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
            
            # ipa 파일 다운로드 링크 및 파일명 찾기
            download_url = ""
            size = 0
            filename = ""
            for asset in data['assets']:
                if asset['name'].endswith('.ipa'):
                    download_url = asset['browser_download_url']
                    size = asset['size']
                    filename = asset['name']
                    break
    except Exception as e:
        print("릴리즈 정보를 가져오는데 실패했습니다:", e)
        return

    if not download_url:
        print("최신 릴리즈에 .ipa 파일이 없습니다.")
        return

    # 🔥 메인 앱 버전 추출 (예: "21.10.2")
    version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', filename)
    if not version_match:
        version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', release_title)
    
    latest_version = version_match.group(1) if version_match else data['tag_name'].lstrip('v')

    # 🔥 트윅 버전 추출 및 설명글 만들기
    # 릴리즈 제목을 띄어쓰기 기준으로 나눈 뒤, 맨 마지막 단어(예: "v5.2b4")를 가져옵니다.
    tweak_version = release_title.split()[-1]
    new_description = f"YouTube Plus {tweak_version} 입니다."

    # 2. 내 app.json 읽기
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        apps_data = json.load(f)

    # 3. 버전 비교하기
    current_version = apps_data['apps'][0]['version'].lstrip('v')

    if latest_version != current_version:
        print(f"새로운 버전을 발견했습니다! 앱: {latest_version}, 트윅: {tweak_version}")
        
        # 내 JSON 파일 업데이트
        apps_data['apps'][0]['version'] = latest_version
        apps_data['apps'][0]['versionDate'] = release_date
        apps_data['apps'][0]['downloadURL'] = download_url
        apps_data['apps'][0]['versionDescription'] = new_description # 설명글 자동 업데이트 적용
        
        if size > 0:
            apps_data['apps'][0]['size'] = size
        
        # 4. 수정된 내용 저장하기
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, indent=2, ensure_ascii=False)
        print("app.json 업데이트 완료.")
    else:
        print("이미 최신 버전입니다.")

if __name__ == "__main__":
    update_json()
