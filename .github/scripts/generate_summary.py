import os
import requests
import re

# 從環境變數讀取 GitHub Actions 傳來的資訊
TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
PR_NUMBER = os.environ['PR_NUMBER']

# GitHub API 的通用設定
BASE_URL = "https://api.github.com"
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
# 取得 diff 內容需要特殊的 Accept header
DIFF_HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3.diff'
}

def get_pr_diff():
    """取得 Pull Request 的 diff 內容"""
    url = f"{BASE_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=DIFF_HEADERS)
    response.raise_for_status()
    return response.text

def parse_diff(diff_text):
    """解析 diff 內容，轉換成我們想要的格式"""
    files_changed = {}
    # 按檔案分割 diff
    file_diffs = diff_text.split('diff --git ')
    
    for file_diff in file_diffs[1:]:
        lines = file_diff.split('\n')
        # 取得檔案路徑
        match = re.search(r'a/(.+) b/(.+)', lines[0])
        if not match:
            continue
        file_path = match.group(2)
        
        # 尋找變更的區塊 (hunks)
        hunks = re.finditer(r'@@ -(\d+,\d+) \+(\d+,\d+) @@', file_diff)
        changes = []
        
        content_lines = lines[1:]
        added_lines = {i: line[1:].strip() for i, line in enumerate(content_lines) if line.startswith('+') and not line.startswith('+++')}
        removed_lines = {i: line[1:].strip() for i, line in enumerate(content_lines) if line.startswith('-') and not line.startswith('---')}
        
        # 簡易配對邏輯：將相鄰的新增和刪除行視為一對變更
        # 這是一個簡化的實現，對於複雜的變更可能不完美
        removed_keys = list(removed_lines.keys())
        added_keys = list(added_lines.keys())

        # 為了避免 Markdown 表格語法錯誤，替換管道符號
        def escape_md(text):
            return text.replace('|', '\|')

        for i, key in enumerate(removed_keys):
            before = escape_md(removed_lines[key])
            after = escape_md(added_lines[added_keys[i]]) if i < len(added_keys) else ""
            changes.append({'before': before, 'after': after})

        if not removed_keys and added_keys: # 處理純新增的情況
            for key in added_keys:
                changes.append({'before': "", 'after': escape_md(added_lines[key])})

        if changes:
            files_changed[file_path] = changes
            
    return files_changed

def generate_markdown(files_changed):
    """產生 Markdown 表格"""
    if not files_changed:
        return "此 Pull Request 沒有檢測到可摘要的程式碼變更。"

    md_comment = "### ✨ Pull Request 變更總結\n\n"
    md_comment += "這是一個自動產生的摘要，將變更以表格呈現，方便審查。\n\n"

    for file_path, changes in files_changed.items():
        md_comment += f"#### 檔案：`{file_path}`\n"
        md_comment += "| 變更前 (—) | 變更後 (+) |\n"
        md_comment += "|:---|:---|\n"
        for change in changes:
            md_comment += f"| `{change['before']}` | `{change['after']}` |\n"
        md_comment += "\n"
        
    # GitHub 留言有字數限制，這裡做個簡單的截斷
    if len(md_comment) > 65000:
        md_comment = md_comment[:65000] + "\n\n...(內容過長，已被截斷)..."
        
    return md_comment

def post_comment(comment_body):
    """將產生的 Markdown 作為留言發佈到 PR"""
    url = f"{BASE_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {'body': comment_body}
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()

if __name__ == "__main__":
    try:
        print("1. 正在取得 PR 的 diff 內容...")
        diff = get_pr_diff()
        
        print("2. 正在解析 diff 並建立摘要...")
        changed_files = parse_diff(diff)
        
        print("3. 正在產生 Markdown 格式的留言...")
        markdown_output = generate_markdown(changed_files)
        
        print("4. 正在將摘要發佈到 Pull Request...")
        post_comment(markdown_output)
        
        print("✅ 成功！摘要已發佈。")
    except requests.exceptions.HTTPError as e:
        print(f"❌ 發生錯誤： {e.response.status_code} {e.response.text}")
    except Exception as e:
        print(f"❌ 發生未知錯誤： {e}")
