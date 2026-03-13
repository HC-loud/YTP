import urllib.request
import json
import os
import re

# 🚨 두 개의 레포지토리 주소를 설정합니다.
TARGET_REPO = "diarrhea3/YTLiteDiarrhea"
TWEAK_REPO = "dayanch96/YTLite"
JSON_FILE = "app.json"

def get_tweak_description(tweak_version):
    # YTLite 원본 레포지토리의 릴리즈 목록을 가져옵니다.
    url = f"https://api.github.com/repos/{TWEAK_REPO}/releases"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            releases = json.loads(response.read())
            for release in releases:
                # 릴리즈 제목이나 태그에 tweak_version(예: 5.2b4)이 포함되어 있는지 확인
                if tweak_version in release.get('name', '') or tweak_version in release.get('tag_name', ''):
                    # 찾았다면 해당 릴리즈의 설명(본문)을 반환합니다.
                    return release.get('body', f"YTLite {tweak_version} 업데이트 내용이 없습니다.")
    except Exception as e:
        print("YTLite 릴리즈 정보를 가져오는데 실패했습니다:", e)
    
    # 만약 원본 레포에서 해당 버전을 못 찾았다면 기본 메시지를 반환합니다.
    return f"YTLite {tweak_version} 버전이 적용되었습니다."

def update_json():
    # 1. 메인 레포의 최신 릴리즈 정보 가져오기
    url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            release_date = data['published_at']
            release_title = data['name'] # 예: "21.10.2 YouTubePlus v5.2b4"
            
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

    # 🔥 앱 버전 추출 (예: "21.10.2")
    version_match = re.search(r'^v?(\d+\.\d+(?:\.\d+)?)', release_title)
    latest_version = version_match.group(1) if version_match else data['tag_name'].lstrip('v')

    # 🔥 트윅 버전 추출 (예: "21.10.2 YouTubePlus v5.2b4" 에서 "5.2b4"만 추출)
    # 제목을 띄어쓰기 기준으로 나눈 뒤, 맨 마지막 단어에서 'v'를 제거합니다.
    tweak_version = release_title.split()[-1].lstrip('v')

    # 2. 내 app.json 읽기
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        apps_data = json.load(f)

    # 3. 버전 비교하기
    current_version = apps_data['apps'][0]['version'].lstrip('v')

    if latest_version != current_version:
        print(f"새로운 버전을 발견했습니다! : 앱 {latest_version} (트윅: {tweak_version})")
        
        # 💡 새로 추가된 기능: YTLite 원본 레포에서 설명글 가져오기
        version_description = get_tweak_description(tweak_version)

        # 내 JSON 파일 업데이트
        apps_data['apps'][0]['version'] = latest_version
        apps_data['apps'][0]['versionDate'] = release_date
        apps_data['apps'][0]['downloadURL'] = download_url
        apps_data['apps'][0]['versionDescription'] = version_description # 설명글 적용
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
