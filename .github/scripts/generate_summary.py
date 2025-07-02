import os
import requests
import json
import google.generativeai as genai

# --- 環境變數讀取 (維持不變) ---
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
PR_NUMBER = os.environ['PR_NUMBER']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite-preview-06-17')

# --- API 設定 (維持不變) ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
DIFF_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3.diff'
}

# 設定 Gemini API 金鑰 (維持不變)
genai.configure(api_key=GEMINI_API_KEY)

def get_pr_diff():
    """取得 Pull Request 的 diff 內容 (維持不變)"""
    url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=DIFF_HEADERS)
    response.raise_for_status()
    return response.text[:30000]

def analyze_diff_with_gemini(diff_text):
    """使用 Gemini API 分析 diff，並安全地組合 prompt"""
    if not diff_text.strip():
        return [{"file_path": "N/A", "topic": "無變更", "description": "這個 PR 不包含程式碼變更，或變更過大無法分析。", "code_snippet": ""}]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # *** 變更點 1: 使用純文字模板，避免 f-string 語法錯誤 ***
    # 這是一個純文字模板，可以安全地包含任何特殊字元
    prompt_template = """
    您是一位頂尖的 GitHub 程式碼審查機器人。請仔細分析下方的 Pull Request diff 內容。
    您的任務是：
    1. 對每一個重要的、邏輯獨立的變更，產生一個獨立的分析。
    2. **非常重要**：您的所有回答，必須格式化為一個 JSON 陣列。陣列中的每一個元素都是一個 JSON 物件。
    3. 每個 JSON 物件必須包含**四個** key：
        - `file_path`: (字串) 變更的檔案完整路徑。
        - `topic`: (字串) 用 2 到 5 個字精準總結變更的「主題」。例如："功能新增"、"Bug 修復"、"效能優化"。
        - `description`: (字串) 用一到兩句話詳細「說明」這個變更的內容、原因與目的。
        - `code_snippet`: (字串) 與您的說明**最相關**的那一小段 `diff` 程式碼片段。請務必包含 `@@ ... @@` 那一行，以及 `+` 和 `-` 的程式碼。

    範例輸出格式：
    [
        {
            "file_path": "src/utils/calculator.js",
            "topic": "Bug 修復",
            "description": "修正了除法運算中未處理除數為零的邊界情況，避免程式崩潰。",
            "code_snippet": "@@ -25,7 +25,9 @@\\n function divide(a, b) {\\n-  return a / b;\\n+  if (b === 0) {\\n+    return null;\\n+  }\\n+  return a / b;\\n }"
        }
    ]

    請用「繁體中文」進行分析與回答。

    這是需要分析的 diff 內容：
    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    # *** 變更點 2: 使用安全的 .replace() 方法來填入 diff 內容 ***
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        summary_points = json.loads(cleaned_text)
        if isinstance(summary_points, list):
            return summary_points
        else:
            return [{"topic": "AI 回應格式錯誤", "description": "AI 未能回傳預期的列表格式。", "file_path": "Error", "code_snippet": ""}]
    except (json.JSONDecodeError, Exception) as e:
        print(f"無法解析 AI 回應或 API 出錯: {e}")
        return [{"topic": "AI 分析失敗", "description": f"AI 分析時發生錯誤。\n原始回應:\n{response.text}", "file_path": "Error", "code_snippet": str(e)}]


def post_comment(comment_data):
    """將包含程式碼片段的結構化資料，格式化為指定的 Markdown 格式後再發佈"""
    # *** 變更點 3: 重新加回顯示程式碼片段的邏輯 ***
    # 1. 先建立留言的主要部分
    body = f"""🤖 **AI 分析要點**

**檔案路徑:** `{comment_data.get('file_path', 'N/A')}`
**變更主題:** {comment_data.get('topic', 'N/A')}
**詳細說明:**
{comment_data.get('description', '無說明')}"""

    # 2. 如果有程式碼片段，再將其附加到主要留言後面
    snippet = comment_data.get('code_snippet', '').strip()
    if snippet:
        code_block = f"""

**相關程式碼變更:**
```diff
{snippet}
```"""
        body += code_block

    # 3. 發佈組合好的完整留言
    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {'body': body}
    response = requests.post(url, json=payload, headers=GITHUB_HEADERS)
    try:
        response.raise_for_status()
        print(f"成功發佈留言: {comment_data.get('topic', 'N/A')} @ {comment_data.get('file_path', 'N/A')}")
    except requests.exceptions.HTTPError as e:
        print(f"發佈留言失敗: {e.response.status_code} {e.response.text}")

if __name__ == "__main__":
    # 主執行流程維持不變
    try:
        print("1. 正在取得 PR 的 diff 內容...")
        diff = get_pr_diff()
        
        print("2. 正在呼叫 Gemini API 進行深度分析...")
        analysis_points = analyze_diff_with_gemini(diff)
        
        if not analysis_points:
            print("AI 未回傳任何分析要點。")
        else:
            print(f"3. 分析完成，取得 {len(analysis_points)} 個要點。準備逐一發佈...")
            for point in analysis_points:
                post_comment(point)
        
        print("✅ 所有分析要點已成功發佈！")
    except Exception as e:
        print(f"❌ 發生未知錯誤： {e}")
        post_comment({
            "file_path": "Bot Execution Error",
            "topic": "機器人執行失敗",
            "description": f"Bot 在執行過程中發生嚴重錯誤，無法完成分析：\n`{str(e)}`",
            "code_snippet": ""
        })
