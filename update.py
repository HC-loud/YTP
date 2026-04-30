import urllib.request
import urllib.error
import json
import re
import sys
import os

# ===================================================
# 설정
# ===================================================
TARGET_REPO  = "jaydenjcpy/YouMod"  # IPA를 가져올 깃허브 레포지토리
JSON_FILE    = "app.json"           # 업데이트할 AltStore JSON 파일
MAX_VERSIONS = 5                    # 보관할 최대 과거 버전 수

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash"
# ===================================================


def fetch_json(url: str) -> dict:
    """GitHub API에서 JSON 데이터를 가져옵니다."""
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def parse_version(version_str: str) -> tuple:
    """버전 문자열을 숫자 튜플로 변환합니다. (시맨틱 버전 비교용)"""
    nums = re.findall(r'\d+', version_str)
    return tuple(int(n) for n in nums)


def translate_to_korean(text: str) -> str:
    """
    Gemini API를 이용해 릴리즈 노트를 한국어로 번역합니다.
    API 키가 없거나 실패하면 원문을 그대로 반환합니다.
    """
    if not GEMINI_API_KEY:
        print("[번역] GEMINI_API_KEY가 없습니다. 원문을 사용합니다.")
        return text

    if not text or not text.strip():
        return text

    print("[번역] 릴리즈 노트를 한국어로 번역 중...")

    prompt = (
        "아래는 iOS 앱 트윅(YouTube 커스텀 앱)의 GitHub 릴리즈 노트입니다.\n"
        "한국어로 자연스럽게 번역해주세요.\n\n"
        "번역 규칙:\n"
        "• 마크다운 형식(##, -, * 등)을 그대로 유지하세요.\n"
        "• 버전 번호, URL, 코드, 기술 용어(tweak, IPA, SponsorBlock 등)는 번역하지 마세요.\n"
        "• 번역문만 출력하고 설명이나 주석은 붙이지 마세요.\n\n"
        f"[원문]\n{text}"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = json.dumps({
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            translated = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            print("[번역] 완료!")
            return translated
    except Exception as e:
        print(f"[번역] 실패 ({e}). 원문을 사용합니다.")
        return text


def format_version_description(release_notes: str, release_title: str) -> str:
    """릴리즈 노트가 없을 경우 기본 형식으로 만들어 반환합니다."""
    if release_notes and release_notes.strip():
        return release_notes
    return f"[업데이트]\n• {release_title}"


def get_latest_release() -> dict | None:
    """원작자 레포에서 최신 릴리즈 정보를 가져옵니다."""
    url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
    try:
        data = fetch_json(url)
    except urllib.error.HTTPError as e:
        print(f"[오류] 릴리즈 정보를 가져오는데 실패했습니다: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"[오류] 릴리즈 정보를 가져오는데 실패했습니다: {e}")
        return None

    # IPA 에셋 찾기
    ipa_asset = next(
        (a for a in data.get("assets", []) if a["name"].endswith(".ipa")),
        None
    )
    if not ipa_asset:
        print("[오류] 최신 릴리즈에 .ipa 파일이 없습니다.")
        return None

    filename      = ipa_asset["name"]
    release_title = data.get("name", "")
    release_body  = data.get("body", "").strip()

    # 앱 버전 추출 (파일명 우선, 없으면 릴리즈 제목, 없으면 태그)
    ver_match = (
        re.search(r'(\d+\.\d+(?:\.\d+)?)', filename) or
        re.search(r'(\d+\.\d+(?:\.\d+)?)', release_title)
    )
    app_version   = ver_match.group(1) if ver_match else data["tag_name"].lstrip("v")
    tweak_version = release_title.split()[-1] if release_title else app_version

    # 릴리즈 노트 한국어 번역
    translated_body     = translate_to_korean(release_body)
    version_description = format_version_description(translated_body, release_title)

    return {
        "app_version":         app_version,
        "tweak_version":       tweak_version,
        "release_date":        data["published_at"],
        "release_title":       release_title,
        "version_description": version_description,
        "download_url":        ipa_asset["browser_download_url"],
        "size":                ipa_asset["size"],
    }


def update_json():
    print(f"[정보] 레포지토리: {TARGET_REPO}")

    release = get_latest_release()
    if not release:
        sys.exit(1)

    latest_version = release["app_version"]
    print(f"[정보] 최신 릴리즈: {latest_version} / 트윅: {release['tweak_version']}")

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            apps_data = json.load(f)
    except FileNotFoundError:
        print(f"[오류] {JSON_FILE} 파일을 찾을 수 없습니다.")
        sys.exit(1)

    app_root        = apps_data["apps"][0]
    current_version = app_root.get("version", "0.0.0").lstrip("v")

    if parse_version(latest_version) <= parse_version(current_version):
        print(f"[정보] 이미 최신 버전입니다. ({current_version})")
        return

    print(f"[업데이트] {current_version} → {latest_version}")

    version_description = release["version_description"]

    new_version_entry = {
        "version":              latest_version,
        "date":                 release["release_date"],
        "localizedDescription": version_description,
        "downloadURL":          release["download_url"],
        "size":                 release["size"],
    }

    existing_versions = app_root.get("versions", [])
    existing_versions = [v for v in existing_versions if v.get("version") != latest_version]
    updated_versions  = ([new_version_entry] + existing_versions)[:MAX_VERSIONS]
    app_root["versions"] = updated_versions

    app_root["version"]            = latest_version
    app_root["versionDate"]        = release["release_date"]
    app_root["versionDescription"] = version_description
    app_root["downloadURL"]        = release["download_url"]
    app_root["size"]               = release["size"]

    apps_data["description"] = f"YouTube Plus {release['tweak_version']} 입니다."

    apps_data["news"] = [{
        "title":      f"{latest_version} - YouTube",
        "identifier": f"news-{latest_version}",
        "caption":    "Update of YTPlus just got released!",
        "date":       release["release_date"],
        "tintColor":  "#FF0000",
        "appID":      "com.google.ios.youtube",
        "notify":     True,
    }]

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(apps_data, f, indent=2, ensure_ascii=False)

    print(f"[완료] app.json 업데이트 완료! (버전 이력 {len(updated_versions)}개 유지)")


if __name__ == "__main__":
    update_json()
