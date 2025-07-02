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
                # 保持完整的 patch 格式，不截斷
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
                    # 對於重要文件，保留更多內容
                    if filename.lower().endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c')):
                        file_section += file_data['patch'][:5000]  # 重要文件保留更多內容
                    else:
                        file_section += file_data['patch'][:2000]  # 其他文件適度保留
                
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
        return [{"file_path": "N/A", "topic": "無變更", "description": "這個 PR 不包含程式碼變更，或變更過大無法分析。", "code_snippet": "", "priority": "Low", "suggestion": ""}]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # 改進的 prompt，提供完整的程式碼差異
    prompt_template = """
    您是一位專業的 GitHub 程式碼審查專家。請仔細分析下方的 Pull Request diff 內容，提供專業且實用的程式碼審查建議。

    **重要的 JSON 格式要求：**
    1. 必須回傳有效的 JSON 陣列格式
    2. 所有字串值中的特殊字符必須正確轉義（使用 \\n 表示換行）
    3. code_snippet 要包含完整的相關變更，不要截斷
    4. 保持原始的 diff 格式，包含 @@、+ 和 - 符號

    **分析要求：**
    1. 關注程式碼品質、安全性、效能和最佳實踐
    2. 提供具體的改進建議
    3. 評估變更的重要性和優先級
    4. 專注於程式碼文件變更，忽略純文檔變更（除非涉及重要配置）

    **回應格式：**每個物件包含以下 6 個欄位：
    - `file_path`: 檔案路徑
    - `topic`: 變更類型（如："新增功能"、"Bug修復"、"效能優化"、"安全性改進"、"配置變更"）
    - `description`: 詳細分析變更內容和影響
    - `priority`: 優先級（"High"、"Medium"、"Low"）
    - `suggestion`: 具體的改進建議（如果沒有建議可填 ""）
    - `code_snippet`: 完整的相關 diff 程式碼片段，保持原始格式，包含足夠的上下文

    **程式碼片段要求：**
    - 保留完整的 diff 格式（@@ 行號信息、+ 和 - 前綴）
    - 包含足夠的上下文（變更前後的相關程式碼）
    - 不要人為截斷，顯示完整的邏輯區塊
    - 正確轉義特殊字符（\\n、\\t、\\"等）

    範例輸出：
    [
        {
            "file_path": "src/components/Example.js",
            "topic": "新增功能",
            "description": "新增了使用者認證組件，提供登入和登出功能。",
            "priority": "Medium",
            "suggestion": "建議加入錯誤處理和載入狀態顯示。",
            "code_snippet": "@@ -10,4 +10,12 @@\\n import React from 'react';\\n\\n+const handleLogin = async (credentials) => {\\n+  try {\\n+    const result = await authService.login(credentials);\\n+    setUser(result.user);\\n+    return { success: true };\\n+  } catch (error) {\\n+    console.error('Login failed:', error);\\n+    return { success: false, error };\\n+  }\\n+};"
        }
    ]

    請用繁體中文分析以下 diff，並確保提供完整的程式碼片段：

    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        print("正在呼叫 Gemini API...")
        print(f"發送給 AI 的 diff 長度: {len(diff_text)} 字符")
        print(f"Diff 開頭預覽: {diff_text[:500]}...")
        
        response = model.generate_content(prompt)
        print(f"Gemini API 回應長度: {len(response.text) if response.text else 0}")
        
        if not response.text:
            return [{"topic": "AI 無回應", "description": "Gemini API 沒有返回任何內容，可能是因為內容過長或 API 限制", "file_path": "Error", "code_snippet": "", "priority": "Medium", "suggestion": "嘗試縮短 diff 內容或檢查 API 設定"}]
        
        # 清理回應文本
        cleaned_text = response.text.strip()
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        
        print(f"清理後的回應預覽: {cleaned_text[:500]}...")
        
        # 嘗試解析 JSON
        try:
            summary_points = json.loads(cleaned_text)
            print(f"成功解析 JSON，包含 {len(summary_points)} 個項目")
        except json.JSONDecodeError as parse_error:
            print(f"JSON 解析失敗: {parse_error}")
            print("嘗試進行字符清理...")
            
            # 移除可能有問題的控制字符，但保留正常的轉義字符
            import re
            cleaned_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', cleaned_text)
            
            try:
                summary_points = json.loads(cleaned_text)
                print(f"清理後成功解析 JSON，包含 {len(summary_points)} 個項目")
            except json.JSONDecodeError as second_error:
                print(f"第二次解析也失敗: {second_error}")
                
                # 顯示調試信息
                debug_text = cleaned_text[:2000] if len(cleaned_text) > 2000 else cleaned_text
                print(f"問題內容: {debug_text}")
                
                # 提供回退結果
                return [{
                    "topic": "JSON 解析錯誤",
                    "description": f"AI 分析成功但回應格式錯誤。主要涉及多個文件的程式碼變更，包括新增功能和架構調整。錯誤: {str(second_error)[:100]}",
                    "file_path": "Multiple Files",
                    "code_snippet": "# 由於 JSON 格式問題，無法顯示完整的程式碼差異\n# 請查看 PR 的 Files changed 標籤頁獲取完整變更",
                    "priority": "Medium",
                    "suggestion": "建議手動檢查 PR 中的主要變更，或重新執行 AI 分析"
                }]
        
        if isinstance(summary_points, list):
            print(f"成功解析 {len(summary_points)} 個分析要點")
            return summary_points
        else:
            return [{"topic": "格式錯誤", "description": "AI 回應不是預期的列表格式", "file_path": "Error", "code_snippet": "", "priority": "Low", "suggestion": ""}]
            
    except Exception as e:
        print(f"API 呼叫錯誤: {e}")
        return [{"topic": "API 錯誤", "description": f"呼叫 Gemini API 時發生錯誤: {str(e)}", "file_path": "Error", "code_snippet": "", "priority": "Low", "suggestion": ""}]

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
        'High': '🔴 **High Priority**',
        'Medium': '🟡 **Medium Priority**', 
        'Low': '🟢 **Low Priority**'
    }
    
    # 主要內容
    body = f"""## 🤖 AI 程式碼審查建議

{priority_badges.get(priority, '🟡 **Medium Priority**')}

### 📁 `{file_path}`

**變更類型：** {topic}

**分析說明：**
{description}"""

    # 添加建議區塊（如果有建議）
    if suggestion.strip():
        body += f"""

**💡 建議改進：**
> {suggestion}"""

    # 添加程式碼變更區塊（如果有程式碼片段）- 不使用折疊，直接顯示
    if snippet:
        body += f"""

### 📋 相關程式碼變更

```diff
{snippet}
```"""
    
    # 添加底部分隔線
    body += "\n\n---\n*由 AI 程式碼審查助手自動生成*"

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
            "description": f"Bot 在執行過程中發生嚴重錯誤，請檢查配置和權限設定。",
            "priority": "High",
            "suggestion": "請檢查 GitHub Actions 日誌獲取詳細錯誤信息，並確認所有必要的環境變數都已正確設定。",
            "code_snippet": f"錯誤詳情: {str(e)}"
        })
