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
        return [{"file_path": "N/A", "topic": "無變更", "description": "這個 PR 不包含程式碼變更，或變更過大無法分析。", "code_snippet": "", "priority": "Low", "suggestion": ""}]

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # 改進的 prompt，減少 JSON 解析問題
    prompt_template = """
    您是一位專業的 GitHub 程式碼審查專家。請仔細分析下方的 Pull Request diff 內容，提供專業且實用的程式碼審查建議。

    **重要的 JSON 格式要求：**
    1. 必須回傳有效的 JSON 陣列格式
    2. 所有字串值中的特殊字符必須正確轉義
    3. code_snippet 中的程式碼要保持簡潔，避免過長的片段
    4. 不要在 JSON 中包含控制字符或未轉義的換行符

    **分析要求：**
    1. 關注程式碼品質、安全性、效能和最佳實踐
    2. 提供具體的改進建議
    3. 評估變更的重要性和優先級
    4. 專注於程式碼文件變更，忽略純文檔變更（除非涉及重要配置）

    **回應格式：**每個物件包含以下 6 個欄位：
    - `file_path`: 檔案路徑
    - `topic`: 變更類型（如："新增功能"、"Bug修復"、"效能優化"、"安全性改進"）
    - `description`: 詳細分析變更內容和影響
    - `priority`: 優先級（"High"、"Medium"、"Low"）
    - `suggestion`: 具體的改進建議（如果沒有建議可填 ""）
    - `code_snippet`: 相關的關鍵程式碼片段 (最多5行)

    範例輸出：
    [
        {
            "file_path": "src/components/Example.js",
            "topic": "新增功能",
            "description": "新增了使用者認證組件，提供登入和登出功能。",
            "priority": "Medium",
            "suggestion": "建議加入錯誤處理和載入狀態顯示。",
            "code_snippet": "+const handleLogin = async (credentials) => {\\n+  const result = await authService.login(credentials);\\n+  setUser(result.user);\\n+};"
        }
    ]

    請用繁體中文分析以下 diff，並確保 JSON 格式正確：

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
            return [{"topic": "AI 無回應", "description": "Gemini API 沒有返回任何內容，可能是因為內容過長或 API 限制", "file_path": "Error", "code_snippet": "", "priority": "Medium", "suggestion": "嘗試縮短 diff 內容或檢查 API 設定"}]
        
        # 清理回應文本
        cleaned_text = response.text.strip()
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        
        print(f"清理後的回應預覽: {cleaned_text[:300]}...")
        
        # 嘗試解析 JSON
        try:
            summary_points = json.loads(cleaned_text)
        except json.JSONDecodeError as parse_error:
            print(f"JSON 解析失敗: {parse_error}")
            print("嘗試進行字符清理...")
            
            # 移除可能有問題的控制字符
            import re
            cleaned_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', cleaned_text)
            
            try:
                summary_points = json.loads(cleaned_text)
            except json.JSONDecodeError as second_error:
                print(f"第二次解析也失敗: {second_error}")
                
                # 顯示調試信息
                debug_text = cleaned_text[:1000] if len(cleaned_text) > 1000 else cleaned_text
                print(f"問題內容: {debug_text}")
                
                # 提供回退結果
                return [{
                    "topic": "JSON 解析錯誤",
                    "description": f"AI 分析成功但回應格式錯誤。錯誤信息: {str(second_error)}",
                    "file_path": "Multiple Files",
                    "code_snippet": "無法顯示程式碼片段",
                    "priority": "Medium",
                    "suggestion": "建議檢查 API 設定或重新執行分析"
                }]
        
        if isinstance(summary_points, list):
            print(f"成功解析 {len(summary_points)} 個分析要點")
            return summary_points
        else:
            return [{"topic": "格式錯誤", "description": "AI 回應不是預期的列表格式", "file_path": "Error", "code_snippet": "", "priority": "Low", "suggestion": ""}]
            
    except Exception as e:
        print(f"API 呼叫錯誤: {e}")
        return [{"topic": "API 錯誤", "description": f"呼叫 Gemini API 時發生錯誤: {str(e)}", "file_path": "Error", "code_snippet": "", "priority": "Low", "suggestion": ""}]

# === 新增的增強功能 ===
def generate_enhanced_diff_html(code_snippet, file_path):
    """生成增強型的程式碼diff HTML"""
    
    # 取得檔案副檔名來決定圖示
    def get_file_icon(filepath):
        ext = filepath.split('.')[-1].lower() if '.' in filepath else 'file'
        icon_map = {
            'js': ('JS', '#f7df1e', '#000'),
            'jsx': ('JSX', '#61dafb', '#000'),
            'ts': ('TS', '#3178c6', '#fff'),
            'tsx': ('TSX', '#3178c6', '#fff'),
            'py': ('PY', '#3776ab', '#fff'),
            'html': ('HTML', '#e34c26', '#fff'),
            'css': ('CSS', '#1572b6', '#fff'),
            'json': ('JSON', '#292929', '#fff'),
            'md': ('MD', '#083fa1', '#fff'),
            'txt': ('TXT', '#6e7681', '#fff')
        }
        return icon_map.get(ext, ('FILE', '#6e7681', '#fff'))
    
    # 改進的diff解析
    def parse_diff_lines(diff_text):
        lines = diff_text.split('\n')
        parsed = []
        line_num = 1
        
        for line in lines:
            line_type = 'context'
            display_line = line
            
            # 識別diff標記
            if line.startswith('@@'):
                line_type = 'hunk'
            elif line.startswith('+') and not line.startswith('+++'):
                line_type = 'added'
                display_line = line[1:]  # 移除 + 符號來顯示純程式碼
            elif line.startswith('-') and not line.startswith('---'):
                line_type = 'removed'  
                display_line = line[1:]  # 移除 - 符號來顯示純程式碼
            elif line.startswith('\\'):
                line_type = 'meta'  # 元資訊行如 "\ No newline at end of file"
            
            parsed.append({
                'content': display_line,
                'type': line_type,
                'number': line_num
            })
            line_num += 1
        
        return parsed
    
    # 改進的語法高亮函數
    def highlight_syntax(code):
        import re
        import html
        
        # 先轉義HTML特殊字符
        code = html.escape(code)
        
        # 關鍵字高亮 - 更精確的匹配
        keywords = ['import', 'export', 'const', 'let', 'var', 'function', 'class', 
                   'if', 'else', 'for', 'while', 'return', 'async', 'await', 'def', 
                   'from', 'try', 'except', 'finally', 'with', 'as', 'in']
        
        # 按長度排序，避免短關鍵字被長關鍵字覆蓋
        keywords.sort(key=len, reverse=True)
        
        for keyword in keywords:
            # 只匹配完整的詞彙邊界
            pattern = r'\b' + re.escape(keyword) + r'\b'
            code = re.sub(pattern, f'<span style="color: #ff7b72;">{keyword}</span>', code)
        
        # 字串高亮 - 處理單引號和雙引號
        code = re.sub(r'(&quot;)([^&quot;]*)(&quot;)', r'<span style="color: #a5d6ff;">\1\2\3</span>', code)
        code = re.sub(r'(&#x27;)([^&#x27;]*)(&#x27;)', r'<span style="color: #a5d6ff;">\1\2\3</span>', code)
        
        # 註解高亮
        code = re.sub(r'(//.*?$|#.*?$)', r'<span style="color: #8b949e;">\1</span>', code, flags=re.MULTILINE)
        
        # 函數名高亮
        code = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()', r'<span style="color: #d2a8ff;">\1</span>', code)
        
        return code
    
    if not code_snippet.strip():
        return "<p><em>沒有程式碼片段可顯示</em></p>"
    
    icon_text, bg_color, text_color = get_file_icon(file_path)
    parsed_lines = parse_diff_lines(code_snippet)
    
    # 計算統計
    additions = sum(1 for line in parsed_lines if line['type'] == 'added')
    deletions = sum(1 for line in parsed_lines if line['type'] == 'removed')
    
    # 生成HTML
    html = f'''
<div style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; 
            border: 1px solid #30363d; border-radius: 6px; overflow: hidden; 
            background: #0d1117; margin: 8px 0;">
    
    <!-- 檔案標題列 -->
    <div style="background: #161b22; padding: 8px 12px; border-bottom: 1px solid #21262d; 
                display: flex; align-items: center; gap: 8px;">
        <div style="background: {bg_color}; color: {text_color}; 
                    padding: 2px 6px; border-radius: 3px; font-size: 10px; 
                    font-weight: bold; min-width: 32px; text-align: center;">
            {icon_text}
        </div>
        <span style="color: #58a6ff; font-weight: 600; font-size: 14px;">
            {file_path}
        </span>
        <div style="margin-left: auto; display: flex; gap: 8px; font-size: 12px;">
            <span style="color: #3fb950;">+{additions}</span>
            <span style="color: #f85149;">-{deletions}</span>
        </div>
    </div>
    
    <!-- 程式碼內容 -->
    <div style="max-height: 400px; overflow-y: auto;">'''
    
    for line_data in parsed_lines:
        line_content = highlight_syntax(line_data['content'])
        line_type = line_data['type']
        line_number = line_data['number']
        
        # 根據類型設定樣式
        if line_type == 'added':
            bg_style = 'background: rgba(46, 160, 67, 0.15); border-left: 3px solid #3fb950;'
        elif line_type == 'removed':
            bg_style = 'background: rgba(248, 81, 73, 0.15); border-left: 3px solid #f85149;'
        elif line_type == 'hunk':
            bg_style = 'background: #21262d; color: #8b949e; font-weight: 600;'
        else:
            bg_style = 'background: transparent;'
        
        html += f'''
        <div style="display: flex; min-height: 20px; font-size: 12px; {bg_style}">
            <div style="background: #161b22; color: #656d76; padding: 0 8px; 
                       min-width: 50px; text-align: right; border-right: 1px solid #21262d;">
                {line_number}
            </div>
            <div style="flex: 1; padding: 0 8px; white-space: pre; color: #c9d1d9;">
                {line_content}
            </div>
        </div>'''
    
    html += '''
    </div>
</div>'''
    
    return html

def post_comment_enhanced(comment_data):
    """發佈增強版的分析結果到 PR"""
    
    # 獲取數據
    file_path = comment_data.get('file_path', 'N/A')
    topic = comment_data.get('topic', 'N/A')
    description = comment_data.get('description', '無說明')
    suggestion = comment_data.get('suggestion', '')
    priority = comment_data.get('priority', 'Medium')
    snippet = comment_data.get('code_snippet', '').strip()
    
    # 優先級樣式
    priority_styles = {
        'High': ('🔴', '#d1242f', '#ffffff'),
        'Medium': ('🟡', '#bf8700', '#ffffff'), 
        'Low': ('🟢', '#1a7f37', '#ffffff')
    }
    
    emoji, bg_color, text_color = priority_styles.get(priority, ('🟡', '#bf8700', '#ffffff'))
    
    # 主要內容
    body = f"""## 🤖 AI 程式碼審查建議

<div style="display: inline-block; background: {bg_color}; color: {text_color}; 
           padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; margin: 4px 0;">
    {emoji} {priority} Priority
</div>

### 📁 檔案路徑
```
{file_path}
```

### 🔍 變更類型
**{topic}**

### 📝 分析說明
{description}"""

    # 添加建議區塊（如果有建議）
    if suggestion.strip():
        body += f"""

### 💡 改進建議
> {suggestion}"""

    # 添加增強型程式碼變更區塊
    if snippet:
        enhanced_diff = generate_enhanced_diff_html(snippet, file_path)
        
        body += f"""

### 📋 程式碼變更詳情

<details>
<summary><strong>點擊展開檢視程式碼差異</strong></summary>

{enhanced_diff}

</details>"""
    
    # 添加底部標識
    body += "\n\n---\n*🤖 由 AI 程式碼審查助手自動生成 | 點擊上方 Details 展開檢視*"

    # 發送請求
    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {'body': body}
    response = requests.post(url, json=payload, headers=GITHUB_HEADERS)
    
    try:
        response.raise_for_status()
        print(f"✅ 成功發佈增強版留言: {topic} @ {file_path}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ 發佈留言失敗: {e.response.status_code}")
        print(f"錯誤詳情: {e.response.text}")

# 保留原本的 post_comment 函數供備用
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

    # 添加程式碼變更區塊（如果有程式碼片段）
    if snippet:
        body += f"""

### 📋 相關程式碼變更

<details>
<summary>點擊查看程式碼差異</summary>

```diff
{snippet}
```

</details>"""
    
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
            
            # 🚀 這裡是關鍵修改：使用增強版留言函數
            USE_ENHANCED_DISPLAY = True  # 設定為 True 使用增強版顯示
            
            for i, point in enumerate(analysis_points, 1):
                print(f"\n發佈第 {i} 個分析要點...")
                
                if USE_ENHANCED_DISPLAY:
                    post_comment_enhanced(point)  # 使用增強版
                else:
                    post_comment(point)  # 使用原版
        
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
