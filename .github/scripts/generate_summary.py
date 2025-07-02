import os
import requests
import json
import google.generativeai as genai

# --- 環境變數讀取 ---
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
PR_NUMBER = os.environ['PR_NUMBER']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite-preview-06-17')

# --- API 設定 ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# 設定 Gemini API 金鑰
genai.configure(api_key=GEMINI_API_KEY)

def get_pr_files():
    """獲取 PR 中所有變更的文件列表"""
    url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=GITHUB_HEADERS)
    response.raise_for_status()
    return response.json()

def get_file_diff(file_data):
    """為單個文件獲取詳細的 diff"""
    # 如果 API 已經提供了 patch，直接使用
    if 'patch' in file_data and file_data['patch']:
        return file_data['patch']
    
    # 否則嘗試獲取完整的文件 diff
    filename = file_data['filename']
    sha = file_data['sha'] if 'sha' in file_data else None
    
    # 為這個文件構建 diff 信息
    diff_info = f"--- a/{filename}\n+++ b/{filename}\n"
    if 'patch' in file_data:
        diff_info += file_data['patch']
    
    return diff_info

def get_pr_diff():
    """取得 Pull Request 的完整 diff 內容"""
    try:
        # 首先獲取 PR 的基本信息
        pr_url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
        pr_response = requests.get(pr_url, headers=GITHUB_HEADERS)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        
        print(f"PR 標題: {pr_data.get('title', 'N/A')}")
        print(f"變更文件數: {pr_data.get('changed_files', 'N/A')}")
        print(f"新增行數: +{pr_data.get('additions', 'N/A')}")
        print(f"刪除行數: -{pr_data.get('deletions', 'N/A')}")
        
        # 獲取所有變更的文件
        files = get_pr_files()
        print(f"實際獲取到 {len(files)} 個變更文件")
        
        if not files:
            return "No files changed in this PR."
        
        # 建構完整的 diff
        full_diff = f"Pull Request: {pr_data.get('title', '')}\n"
        full_diff += f"Files changed: {len(files)}\n"
        full_diff += f"Additions: +{pr_data.get('additions', 0)}, Deletions: -{pr_data.get('deletions', 0)}\n\n"
        
        # 處理每個文件
        for file_data in files:
            filename = file_data['filename']
            status = file_data['status']  # added, modified, removed, renamed
            additions = file_data.get('additions', 0)
            deletions = file_data.get('deletions', 0)
            
            print(f"處理文件: {filename} (狀態: {status}, +{additions}/-{deletions})")
            
            file_diff = f"\n{'='*50}\n"
            file_diff += f"File: {filename}\n"
            file_diff += f"Status: {status}\n"
            file_diff += f"Changes: +{additions}/-{deletions}\n"
            file_diff += f"{'='*50}\n"
            
            # 獲取文件的 diff 內容
            if 'patch' in file_data and file_data['patch']:
                file_diff += file_data['patch']
            else:
                file_diff += f"(No patch data available for {filename})"
            
            full_diff += file_diff + "\n"
        
        # 智能截斷：優先保留重要文件的 diff
        if len(full_diff) > 25000:  # 稍微降低限制以留出空間
            print(f"⚠️  Diff 內容過長 ({len(full_diff)} 字符)，進行智能截斷...")
            
            # 按文件重要性排序（非 .md 文件優先）
            important_files = []
            less_important_files = []
            
            for file_data in files:
                filename = file_data['filename'].lower()
                if (filename.endswith('.py') or filename.endswith('.js') or 
                    filename.endswith('.ts') or filename.endswith('.java') or
                    filename.endswith('.go') or filename.endswith('.rs') or
                    filename.endswith('.cpp') or filename.endswith('.c')):
                    important_files.append(file_data)
                else:
                    less_important_files.append(file_data)
            
            # 重新構建 diff，優先包含重要文件
            truncated_diff = f"Pull Request: {pr_data.get('title', '')}\n"
            truncated_diff += f"Files changed: {len(files)} (showing important files first)\n\n"
            
            current_length = len(truncated_diff)
            files_included = 0
            
            # 先添加重要文件
            for file_data in important_files + less_important_files:
                if current_length > 20000:  # 留出一些空間
                    break
                    
                filename = file_data['filename']
                file_section = f"\nFile: {filename}\n"
                if 'patch' in file_data and file_data['patch']:
                    file_section += file_data['patch'][:2000]  # 每個文件最多 2000 字符
                
                if current_length + len(file_section) < 25000:
                    truncated_diff += file_section
                    current_length += len(file_section)
                    files_included += 1
                else:
                    break
            
            if files_included < len(files):
                truncated_diff += f"\n\n⚠️ 注意: 只顯示了 {files_included}/{len(files)} 個文件的變更內容"
            
            return truncated_diff
        
        print(f"完整 diff 長度: {len(full_diff)} 字符")
        return full_diff
        
    except Exception as e:
        print(f"獲取 PR diff 時發生錯誤: {e}")
        return f"Error fetching PR diff: {str(e)}"

def analyze_diff_with_gemini(diff_text):
    """使用 Gemini API 分析 diff"""
    if not diff_text.strip():
        return [{"file_path": "N/A", "topic": "無變更", "description": "這個 PR 不包含程式碼變更，或變更過大無法分析。", "code_snippet": ""}]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # 添加更詳細的 prompt
    prompt_template = """
    您是一位頂尖的 GitHub 程式碼審查機器人。請仔細分析下方的 Pull Request diff 內容。

    **重要指示：**
    1. 請關注所有類型的文件變更，不只是 markdown 文件
    2. 優先分析程式碼文件 (.py, .js, .ts, .java, .go 等) 的變更
    3. 對每一個重要的、邏輯獨立的變更，產生一個獨立的分析
    4. **必須**格式化為 JSON 陣列回應

    您的任務是：
    1. 識別所有重要的變更（程式碼邏輯、新功能、bug 修復、配置變更等）
    2. 為每個重要變更創建一個分析條目
    3. 每個 JSON 物件必須包含四個 key：
        - `file_path`: (字串) 變更的檔案完整路徑
        - `topic`: (字串) 用 2-5 個字精準總結變更主題
        - `description`: (字串) 詳細說明變更內容、原因與影響
        - `code_snippet`: (字串) 最相關的 diff 程式碼片段

    範例輸出：
    [
        {
            "file_path": "src/main.py",
            "topic": "新增功能",
            "description": "新增了使用者驗證功能，包含密碼加密和 JWT token 生成機制。",
            "code_snippet": "@@ -10,0 +11,5 @@\\n+def authenticate_user(username, password):\\n+    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())\\n+    # 驗證邏輯\\n+    return generate_jwt_token(username)"
        }
    ]

    請用「繁體中文」分析，並特別關注程式碼變更：

    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        print("正在呼叫 Gemini API...")
        response = model.generate_content(prompt)
        print(f"Gemini API 回應長度: {len(response.text) if response.text else 0}")
        
        if not response.text:
            return [{"topic": "AI 無回應", "description": "Gemini API 沒有返回任何內容", "file_path": "Error", "code_snippet": ""}]
            
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        print(f"清理後的回應預覽: {cleaned_text[:200]}...")
        
        summary_points = json.loads(cleaned_text)
        if isinstance(summary_points, list):
            print(f"成功解析 {len(summary_points)} 個分析要點")
            return summary_points
        else:
            return [{"topic": "格式錯誤", "description": "AI 回應不是預期的列表格式", "file_path": "Error", "code_snippet": ""}]
            
    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤: {e}")
        print(f"原始回應: {response.text[:500] if response.text else 'None'}")
        return [{"topic": "解析失敗", "description": f"無法解析 AI 回應為 JSON 格式", "file_path": "Error", "code_snippet": str(e)}]
    except Exception as e:
        print(f"API 呼叫錯誤: {e}")
        return [{"topic": "API 錯誤", "description": f"呼叫 Gemini API 時發生錯誤: {str(e)}", "file_path": "Error", "code_snippet": ""}]


def post_comment(comment_data):
    """發佈分析結果到 PR"""
    body = f"""🤖 **AI 分析要點**

**檔案路徑:** `{comment_data.get('file_path', 'N/A')}`
**變更主題:** {comment_data.get('topic', 'N/A')}
**詳細說明:**
{comment_data.get('description', '無說明')}"""

    snippet = comment_data.get('code_snippet', '').strip()
    if snippet:
        body += f"""

**相關程式碼變更:**
```diff
{snippet}
```"""

    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {'body': body}
    response = requests.post(url, json=payload, headers=GITHUB_HEADERS)
    
    try:
        response.raise_for_status()
        print(f"✅ 成功發佈留言: {comment_data.get('topic', 'N/A')} @ {comment_data.get('file_path', 'N/A')}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ 發佈留言失敗: {e.response.status_code}")
        print(f"錯誤詳情: {e.response.text}")

if __name__ == "__main__":
    try:
        print("🚀 開始分析 Pull Request...")
        print("=" * 50)
        
        print("1. 正在取得 PR 的 diff 內容...")
        diff = get_pr_diff()
        
        if not diff or len(diff.strip()) < 50:
            print("⚠️  警告: 獲取到的 diff 內容過短或為空")
            print(f"Diff 內容預覽: {diff[:200] if diff else 'None'}")
        
        print("\n2. 正在呼叫 Gemini API 進行深度分析...")
        analysis_points = analyze_diff_with_gemini(diff)
        
        if not analysis_points:
            print("❌ AI 未回傳任何分析要點")
        else:
            print(f"\n3. 分析完成！取得 {len(analysis_points)} 個要點")
            print("準備發佈分析結果...")
            
            for i, point in enumerate(analysis_points, 1):
                print(f"\n發佈第 {i} 個分析要點...")
                post_comment(point)
        
        print("\n" + "=" * 50)
        print("✅ 所有分析要點已成功發佈！")
        
    except Exception as e:
        print(f"\n❌ 發生未知錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 發佈錯誤信息
        post_comment({
            "file_path": "Bot Execution Error",
            "topic": "機器人執行失敗",
            "description": f"Bot 在執行過程中發生嚴重錯誤：\n```\n{str(e)}\n```",
            "code_snippet": ""
        })
