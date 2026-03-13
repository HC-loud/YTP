import urllib.request
import json
import os

# 🚨 여기에 원작자의 깃허브 주소를 넣으세요 (예: qnblackcat/uYouPlus)
TARGET_REPO = "diarrhea3/YTLiteDiarrhea"
JSON_FILE = "app.json"

def update_json():
    # 1. 원작자의 최신 릴리즈 정보 가져오기
    url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            latest_version = data['tag_name'].lstrip('v') # 'v1.0' -> '1.0'
            release_date = data['published_at']
            
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

    # 2. 내 apps.json 읽기
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        apps_data = json.load(f)

    # 3. 버전 비교하기 (내 JSON의 첫 번째 앱 기준)
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
        print("apps.json 업데이트 완료.")
    else:
        print("이미 최신 버전입니다.")

if __name__ == "__main__":
    update_json()
