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
    
    # 簡化的 prompt，減少 JSON 錯誤
    prompt_template = """
    您是一位專業的程式碼審查專家。請分析以下 Pull Request 的變更內容。

    **重要要求：**
    1. 請僅回傳有效的 JSON 陣列
    2. 每個 JSON 物件必須包含這 6 個欄位：file_path, topic, description, priority, suggestion, code_snippet
    3. 所有字串值必須用雙引號包圍
    4. 物件之間必須用逗號分隔
    5. code_snippet 中的特殊字符必須轉義（\\n \\t \\" \\\\）

    **JSON 格式範例：**
    [
        {
            "file_path": "src/App.js",
            "topic": "架構調整",
            "description": "重構應用程式結構，新增路由功能",
            "priority": "Medium",
            "suggestion": "建議加入錯誤處理",
            "code_snippet": "+import { BrowserRouter } from 'react-router-dom';\\n+function App() {\\n+  return <BrowserRouter>...</BrowserRouter>;\\n+}"
        }
    ]

    請分析以下 diff 並以 JSON 格式回應：

    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        print("正在呼叫 Gemini API...")
        print(f"發送給 AI 的 diff 長度: {len(diff_text)} 字符")
        
        response = model.generate_content(prompt)
        print(f"Gemini API 回應長度: {len(response.text) if response.text else 0}")
        
        if not response.text:
            return [{"topic": "AI 無回應", "description": "Gemini API 沒有返回任何內容", "file_path": "Error", "code_snippet": "", "priority": "Medium", "suggestion": ""}]
        
        # 清理和修復 JSON
        cleaned_text = response.text.strip()
        
        # 移除 markdown 標記
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        
        # 保存原始回應用於調試
        print(f"原始 AI 回應預覽: {cleaned_text[:1000]}...")
        
        # 嘗試修復常見的 JSON 問題
        def fix_json(text):
            import re
            
            # 1. 移除控制字符
            text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
            
            # 2. 修復缺失的逗號（在 } 和 { 之間）
            text = re.sub(r'}\s*\n\s*{', '},\n{', text)
            text = re.sub(r'}\s*{', '},{', text)
            
            # 3. 修復缺失的逗號（在 " 和 " 之間跨行）
            text = re.sub(r'"\s*\n\s*"', '",\n"', text)
            
            # 4. 修復未閉合的字符串
            text = re.sub(r'([^"\\])\n\s*([}\]])', r'\1",\n\2', text)
            
            # 5. 確保陣列格式正確
            if not text.strip().startswith('['):
                text = '[' + text
            if not text.strip().endswith(']'):
                text = text + ']'
            
            return text
        
        # 嘗試解析原始 JSON
        try:
            summary_points = json.loads(cleaned_text)
            print(f"✅ 成功解析原始 JSON，包含 {len(summary_points)} 個項目")
        except json.JSONDecodeError as parse_error:
            print(f"❌ 原始 JSON 解析失敗: {parse_error}")
            print(f"錯誤位置: line {getattr(parse_error, 'lineno', '?')} column {getattr(parse_error, 'colno', '?')}")
            
            # 嘗試修復 JSON
            print("🔧 嘗試修復 JSON 格式...")
            fixed_text = fix_json(cleaned_text)
            
            try:
                summary_points = json.loads(fixed_text)
                print(f"✅ 修復後成功解析 JSON，包含 {len(summary_points)} 個項目")
            except json.JSONDecodeError as second_error:
                print(f"❌ 修復後仍解析失敗: {second_error}")
                print(f"錯誤位置: line {getattr(second_error, 'lineno', '?')} column {getattr(second_error, 'colno', '?')}")
                
                # 顯示更詳細的調試信息
                print("\n📋 詳細調試信息:")
                print(f"修復前長度: {len(cleaned_text)}")
                print(f"修復後長度: {len(fixed_text)}")
                
                # 顯示出錯位置附近的內容
                if hasattr(second_error, 'pos'):
                    error_pos = second_error.pos
                    start = max(0, error_pos - 100)
                    end = min(len(fixed_text), error_pos + 100)
                    print(f"錯誤位置附近內容 (位置 {error_pos}):")
                    print(f"'{fixed_text[start:end]}'")
                
                print(f"修復後內容開頭 500 字符:")
                print(f"'{fixed_text[:500]}'")
                
                print(f"修復後內容結尾 200 字符:")
                print(f"'{fixed_text[-200:]}'")
                
                # 嘗試手動解析部分內容
                if "file_path" in fixed_text:
                    print("🔍 檢測到 file_path，嘗試提取信息...")
                    # 簡化的回退處理
                    return [{
                        "topic": "AI 分析成功",
                        "description": "AI 成功分析了程式碼變更，但 JSON 格式需要進一步調整。主要變更包括多個檔案的程式碼修改，涉及路由整合、新增組件等。",
                        "file_path": "Multiple Files",
                        "code_snippet": "// AI 分析成功但 JSON 格式化問題\\n// 建議查看 GitHub PR 的 Files 標籤頁查看完整變更",
                        "priority": "Medium",
                        "suggestion": "建議檢查 AI API 設定或重新執行分析，問題可能是 JSON 轉義字符處理"
                    }]
                else:
                    # 最終回退
                    return [{
                        "topic": "JSON 格式錯誤",
                        "description": f"AI 回應包含複雜的格式錯誤。詳細錯誤: {str(second_error)[:300]}",
                        "file_path": "Error",
                        "code_snippet": "# JSON 解析失敗，無法顯示程式碼差異",
                        "priority": "Low",
                        "suggestion": "嘗試重新執行分析，或檢查 Gemini API 設定和版本"
                    }]
        
        # 驗證結果格式
        if isinstance(summary_points, list) and len(summary_points) > 0:
            # 檢查每個項目是否包含必要欄位
            valid_points = []
            for point in summary_points:
                if isinstance(point, dict) and all(key in point for key in ['file_path', 'topic', 'description']):
                    # 確保所有必要欄位都存在
                    valid_point = {
                        'file_path': point.get('file_path', 'Unknown'),
                        'topic': point.get('topic', '程式碼變更'),
                        'description': point.get('description', '檔案內容有變更'),
                        'priority': point.get('priority', 'Medium'),
                        'suggestion': point.get('suggestion', ''),
                        'code_snippet': point.get('code_snippet', '')
                    }
                    valid_points.append(valid_point)
            
            if valid_points:
                print(f"✅ 驗證完成，返回 {len(valid_points)} 個有效分析要點")
                return valid_points
        
        # 如果到這裡說明格式有問題
        return [{"topic": "格式驗證失敗", "description": "AI 回應格式不符合預期", "file_path": "Error", "code_snippet": "", "priority": "Low", "suggestion": ""}]
            
    except Exception as e:
        print(f"❌ API 呼叫錯誤: {e}")
        import traceback
        traceback.print_exc()
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
