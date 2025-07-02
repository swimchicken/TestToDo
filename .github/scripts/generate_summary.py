import os
import requests
import json
import google.generativeai as genai
import re
import traceback

# --- 環境變數讀取 ---
# 從環境變數中獲取必要的配置信息
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO = os.environ.get('GITHUB_REPOSITORY')
PR_NUMBER = os.environ.get('PR_NUMBER')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
# GEMINI_MODEL 的拼寫錯誤已在環境變數名稱中修正
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite-preview-06-17')

# --- API 設定 ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# 設定 Gemini API 金鑰
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("❌ 錯誤：GEMINI_API_KEY 環境變數未設定。")
    exit(1)


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
    
    # 否則，這表示可能是一個沒有內容變更的文件（例如，僅模式變更）
    filename = file_data.get('filename', 'Unknown file')
    return f"--- a/{filename}\n+++ b/{filename}\n(No patch data provided)"


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
            
            file_diff_content = get_file_diff(file_data)
            
            file_header = f"\n{'='*50}\n"
            file_header += f"File: {filename}\n"
            file_header += f"Status: {status}\n"
            file_header += f"Changes: +{additions}/-{deletions}\n"
            file_header += f"{'='*50}\n"
            
            full_diff += file_header + file_diff_content + "\n"
        
        # 智能截斷：當 diff 過長時，優先保留重要文件的 diff
        # Gemini-1.5-Flash 有很大的上下文窗口，但為避免成本和延遲，仍保留截斷邏輯
        MAX_DIFF_LENGTH = 100000  # 可根據需求調整
        if len(full_diff) > MAX_DIFF_LENGTH:
            print(f"⚠️ Diff 內容過長 ({len(full_diff)} 字符)，進行智能截斷...")
            
            # 按文件重要性排序（程式碼文件優先）
            important_files = []
            less_important_files = []
            
            code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h', '.cs', '.rb', '.php'}
            
            for file_data in files:
                if any(file_data['filename'].lower().endswith(ext) for ext in code_extensions):
                    important_files.append(file_data)
                else:
                    less_important_files.append(file_data)
            
            # 重新構建 diff，優先包含重要文件
            truncated_diff = f"Pull Request: {pr_data.get('title', '')}\n"
            truncated_diff += f"Files changed: {len(files)} (showing important files first due to length limit)\n\n"
            
            current_length = len(truncated_diff)
            files_included = 0
            
            # 每個文件的 diff 內容限制，可以視情況調整
            PER_FILE_CHAR_LIMIT = 5000 

            for file_data in important_files + less_important_files:
                filename = file_data['filename']
                file_patch = get_file_diff(file_data)
                
                # 截斷單一文件的 patch
                if len(file_patch) > PER_FILE_CHAR_LIMIT:
                    file_patch = file_patch[:PER_FILE_CHAR_LIMIT] + "\n... (file content truncated)\n"
                
                file_section = f"\nFile: {filename}\n{file_patch}"

                if current_length + len(file_section) < MAX_DIFF_LENGTH:
                    truncated_diff += file_section
                    current_length += len(file_section)
                    files_included += 1
                else:
                    break
            
            if files_included < len(files):
                truncated_diff += f"\n\n⚠️ 注意: 內容過長，只顯示了 {files_included}/{len(files)} 個文件的變更內容。"
            
            return truncated_diff
        
        print(f"完整 diff 長度: {len(full_diff)} 字符")
        return full_diff
        
    except Exception as e:
        print(f"獲取 PR diff 時發生錯誤: {e}")
        return f"Error fetching PR diff: {str(e)}"


def analyze_diff_with_gemini(diff_text):
    """使用 Gemini API 分析 diff"""
    if not diff_text or not diff_text.strip() or len(diff_text) < 50:
        return [{"file_path": "N/A", "topic": "無有效變更", "description": "這個 PR 不包含有效的程式碼變更，或變更內容過短無法進行分析。", "code_snippet": "", "priority": "Low", "suggestion": ""}]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # --- ✨ 修改點 ✨ ---
    # 修改了 `code_snippet` 的說明，要求 AI 提供完整的 diff 區塊
    prompt_template = """
    您是一位頂尖的軟體工程師與程式碼審查專家。請仔細分析下方的 Pull Request diff 內容，提供專業、簡潔且實用的程式碼審查建議。

    **重要的 JSON 格式要求：**
    1.  **必須**回傳一個有效的 JSON 陣列 `[...]`。
    2.  所有字串值中的特殊字符 (如 `"` 和 `\`) **必須**被正確轉義。
    3.  不要在 JSON 結構之外包含任何文字、註解或 ```json ... ``` 標記。你的回應只能是純粹的 JSON 內容。

    **分析要求：**
    1.  **專注品質**：關注程式碼品質、潛在 Bug、安全性、效能和可讀性。
    2.  **具體建議**：提供清晰、可執行的改進建議。
    3.  **忽略瑣碎變更**：忽略純文檔、格式或不重要的註解變更。
    4.  **合併同類建議**：如果同一個檔案有多個相關的小建議，請合併成一個分析點。

    **回應格式：** 每個陣列中的物件包含以下 6 個欄位：
    - `file_path`: (string) 檔案的完整路徑。
    - `topic`: (string) 總結變更的類型，例如："新增使用者認證功能"、"修復快取失效 Bug"、"重構資料庫查詢邏輯"。
    - `description`: (string) 詳細分析這次變更的內容、目的和潛在影響。
    - `priority`: (string) 根據重要性和緊急性，評估為 "High"、"Medium" 或 "Low"。
    - `suggestion`: (string) 提出具體的改進建議。如果沒有建議，請留空字串 ""。
    - `code_snippet`: (string) **引用與此建議相關的完整 diff 區塊。請包含從 '@@' 開始的標頭行，以及所有相關的 '+' (新增) 和 '-' (刪除) 行。**

    請用繁體中文分析以下 diff，並嚴格遵守上述 JSON 格式要求：

    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        print("正在呼叫 Gemini API...")
        response = model.generate_content(prompt)
        
        if not response.text:
            return [{"topic": "AI 無回應", "description": "Gemini API 沒有返回任何內容，可能是因為內容過長或 API 限制", "file_path": "Error", "code_snippet": "", "priority": "Medium", "suggestion": "嘗試縮短 diff 內容或檢查 API 設定"}]
        
        print(f"Gemini API 回應長度: {len(response.text)}")
        
        # 清理回應文本，移除可能存在的 Markdown 程式碼區塊標記
        cleaned_text = response.text.strip()
        cleaned_text = re.sub(r'^```json\s*', '', cleaned_text)
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        
        print(f"清理後的回應預覽: {cleaned_text[:300]}...")
        
        # 解析 JSON
        summary_points = json.loads(cleaned_text)
        
        if isinstance(summary_points, list):
            print(f"成功解析 {len(summary_points)} 個分析要點")
            return summary_points
        else:
            print("❌ 警告：AI 回應不是預期的列表格式。")
            return [{"topic": "格式錯誤", "description": "AI 回應不是預期的列表格式", "file_path": "Error", "code_snippet": cleaned_text, "priority": "Low", "suggestion": ""}]
            
    except json.JSONDecodeError as parse_error:
        print(f"❌ JSON 解析失敗: {parse_error}")
        return [{
            "topic": "JSON 解析錯誤",
            "description": f"AI 分析成功但回應格式錯誤。請檢查日誌。\n錯誤信息: {str(parse_error)}",
            "file_path": "Multiple Files",
            "code_snippet": cleaned_text, # 將無法解析的原文放入，方便除錯
            "priority": "High",
            "suggestion": "這通常是 AI 未能嚴格遵守 JSON 格式所致。請檢查 Action Log 中的『清理後的回應預覽』以獲取詳細資訊。"
        }]
    except Exception as e:
        print(f"❌ API 呼叫或處理時發生錯誤: {e}")
        return [{"topic": "API 錯誤", "description": f"呼叫 Gemini API 時發生錯誤: {str(e)}", "file_path": "Error", "code_snippet": "", "priority": "High", "suggestion": ""}]


def post_comment(comment_data):
    """發佈專業格式的分析結果到 PR"""
    
    # 獲取數據
    file_path = comment_data.get('file_path', 'N/A')
    topic = comment_data.get('topic', 'N/A')
    description = comment_data.get('description', '無說明')
    suggestion = comment_data.get('suggestion', '')
    priority = comment_data.get('priority', 'Medium')
    snippet = comment_data.get('code_snippet', '').strip()
    
    # 優先級標籤和顏色
    priority_badges = {
        'High': '🔴 **高度優先 (High Priority)**',
        'Medium': '🟡 **中度優先 (Medium Priority)**',
        'Low': '🟢 **低度優先 (Low Priority)**'
    }
    
    # 主要內容
    body = f"""## 🤖 AI Code Review

{priority_badges.get(priority, '🟡 **Medium Priority**')}

### 📁 檔案：`{file_path}`

**主題：{topic}**

**分析說明：**
{description}"""

    # 添加建議區塊（如果有建議）
    if suggestion.strip():
        body += f"""

**💡 改進建議：**
> {suggestion}"""

    # 添加程式碼變更區塊（如果有程式碼片段）
    if snippet:
        body += f"""

### 📋 相關程式碼變更
<details><summary>點擊展開/摺疊程式碼差異</summary>

````diff
{snippet}
"""
# 添加底部分隔線
body += "\n\n---\n*由 Gemini-AI-Code-Review-Bot 自動生成*"

# 發送請求
url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
payload = {'body': body}
response = requests.post(url, json=payload, headers=GITHUB_HEADERS)

try:
    response.raise_for_status()
    print(f"✅ 成功發佈留言: {topic} @ {file_path}")
except requests.exceptions.HTTPError as e:
    print(f"❌ 發佈留言失敗: {e.response.status_code}")
    print(f"錯誤詳情: {e.response.text}")
if name == "main":
if not all([GITHUB_TOKEN, REPO, PR_NUMBER, GEMINI_API_KEY]):
print("❌ 致命錯誤：一個或多個必要的環境變數未設定。")
print("請檢查 GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, GEMINI_API_KEY。")
exit(1)
try:
    print("🚀 開始分析 Pull Request...")
    print("=" * 50)
    
    print("1. 正在取得 PR 的 diff 內容...")
    diff = get_pr_diff()
    
    if not diff or len(diff.strip()) < 10:
        print("✅ 偵測到無程式碼變更或 diff 內容過短，無需分析。")
    else:
        print("\n2. 正在呼叫 Gemini API 進行深度分析...")
        analysis_points = analyze_diff_with_gemini(diff)
        
        if not analysis_points:
            print("❌ AI 未回傳任何分析要點。")
        else:
            print(f"\n3. 分析完成！取得 {len(analysis_points)} 個要點，準備發佈...")
            
            for i, point in enumerate(analysis_points, 1):
                print(f"\n發佈第 {i}/{len(analysis_points)} 個分析要點...")
                post_comment(point)
    
    print("\n" + "=" * 50)
    print("✅ 任務執行完畢！")
    
except Exception as e:
    print(f"\n❌ 發生未預期的嚴重錯誤: {e}")
    error_details = traceback.format_exc()
    print(error_details)
    
    # 發佈錯誤信息到 PR
    post_comment({
        "file_path": "Bot Execution Error",
        "topic": "機器人執行失敗",
        "description": f"Bot 在執行過程中發生嚴重錯誤，請檢查 Actions log。",
        "priority": "High",
        "suggestion": "請檢查 GitHub Actions log 以獲取詳細錯誤信息，並確認所有必要的環境變數都已正確設定。",
        "code_snippet": f"錯誤類型: {type(e).__name__}\n錯誤訊息: {str(e)}\n\nTraceback:\n{error_details[:1000]}"
    })
