import os
import requests
import json
import google.generativeai as genai

# --- 環境變數讀取 ---
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
PR_NUMBER = os.environ['PR_NUMBER']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash-latest')

# --- API 設定 ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
DIFF_HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3.diff'
}

# 設定 Gemini API 金鑰
genai.configure(api_key=GEMINI_API_KEY)

def get_pr_diff():
    """取得 Pull Request 的 diff 內容"""
    url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=DIFF_HEADERS)
    response.raise_for_status()
    # 限制 diff 長度，避免超出模型限制或費用過高
    return response.text[:25000]

def analyze_diff_with_gemini(diff_text):
    """使用 Gemini API 分析 diff 並回傳要點列表"""
    if not diff_text.strip():
        return ["這個 PR 不包含程式碼變更，或變更過大無法分析。"]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # 設計給 AI 的指令 (Prompt)
    prompt = f"""
    您是一位資深的 GitHub 程式碼審查專家。請分析以下 Pull Request 的 diff 內容。
    您的任務是：
    1. 深入理解程式碼的變更。
    2. 總結出幾個最重要的、各自獨立的變更要點（例如：功能新增、Bug 修復、程式碼重構、依賴更新等）。
    3. 每一個要點都必須是完整的句子，並使用 Markdown 格式（例如，用 **粗體** 強調關鍵字）。
    4. **非常重要**：請將您的所有回答格式化為一個 JSON 陣列 (array of strings)，陣列中的每個字串就是一個獨立的變更要點。不要在 JSON 陣列之外包含任何說明文字。

    範例輸出格式：
    ["- **功能新增**: 新增了使用者登出按鈕到導覽列。","- **Bug 修復**: 修正了在個人資料頁面，使用者名稱顯示不正確的問題。"]

    請用「繁體中文」進行分析與回答。

    這是需要分析的 diff 內容：
    ```diff
    {diff_text}
    ```
    """
    
    try:
        response = model.generate_content(prompt)
        # 清理 AI 可能返回的 markdown code block 標籤
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        # 解析 JSON
        summary_points = json.loads(cleaned_text)
        if isinstance(summary_points, list):
            return summary_points
        else:
            return ["AI 回應格式錯誤，無法解析為要點列表。"]
    except (json.JSONDecodeError, Exception) as e:
        print(f"無法解析 AI 回應或 API 出錯: {e}")
        return [f"AI 分析時發生錯誤，無法產生摘要。\n原始回應:\n{response.text}"]


def post_comment(comment_body):
    """將單一留言發佈到 PR"""
    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {'body': comment_body}
    response = requests.post(url, json=payload, headers=GITHUB_HEADERS)
    try:
        response.raise_for_status()
        print(f"成功發佈留言: {comment_body[:50]}...")
    except requests.exceptions.HTTPError as e:
        print(f"發佈留言失敗: {e.response.status_code} {e.response.text}")

if __name__ == "__main__":
    try:
        print("1. 正在取得 PR 的 diff 內容...")
        diff = get_pr_diff()
        
        print("2. 正在呼叫 Gemini API 進行分析...")
        analysis_points = analyze_diff_with_gemini(diff)
        
        if not analysis_points:
            print("AI 未回傳任何分析要點。")
        else:
            print(f"3. 分析完成，取得 {len(analysis_points)} 個要點。準備逐一發佈...")
            # 將每個要點作為獨立留言發佈
            for point in analysis_points:
                post_comment(f"🤖 **AI 分析要點**\n\n{point}")
        
        print("✅ 所有分析要點已成功發佈！")
    except Exception as e:
        print(f"❌ 發生未知錯誤： {e}")
        post_comment(f"🤖 Bot 執行時發生嚴重錯誤，無法完成分析：\n`{str(e)}`")
