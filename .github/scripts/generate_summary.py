import os
import requests
import json
import base64
import google.generativeai as genai
from datetime import datetime

# --- 環境變數讀取 ---
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
PR_NUMBER = os.environ['PR_NUMBER']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite-preview-06-17')

# 設定使用的HTML方案
HTML_STRATEGY = os.environ.get('HTML_STRATEGY', 'github_native')  # github_native, svg_enhanced, gist_report, github_pages

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

def post_comment_github_native_html(comment_data):
    """使用GitHub原生支援的HTML標籤 - 最穩定方案"""
    
    file_path = comment_data.get('file_path', 'N/A')
    topic = comment_data.get('topic', 'N/A')
    description = comment_data.get('description', '無說明')
    suggestion = comment_data.get('suggestion', '')
    priority = comment_data.get('priority', 'Medium')
    snippet = comment_data.get('code_snippet', '').strip()
    
    # 優先級顏色和emoji
    priority_config = {
        'High': ('#d1242f', '🔴', 'HIGH PRIORITY'),
        'Medium': ('#bf8700', '🟡', 'MEDIUM PRIORITY'),
        'Low': ('#1a7f37', '🟢', 'LOW PRIORITY')
    }
    
    color, emoji, label = priority_config.get(priority, ('#bf8700', '🟡', 'MEDIUM PRIORITY'))
    
    # 檔案類型檢測
    def get_file_info(filepath):
        ext = filepath.split('.')[-1].lower() if '.' in filepath else 'file'
        file_types = {
            'js': ('JavaScript', '⚡'), 'jsx': ('React JSX', '⚛️'),
            'ts': ('TypeScript', '🔷'), 'tsx': ('React TSX', '⚛️'),
            'py': ('Python', '🐍'), 'html': ('HTML', '🌐'),
            'css': ('CSS', '🎨'), 'json': ('JSON', '📋'),
            'md': ('Markdown', '📝'), 'yml': ('YAML', '⚙️'),
        }
        return file_types.get(ext, ('File', '📁'))
    
    file_type, file_emoji = get_file_info(file_path)
    
    # 分析程式碼統計
    def analyze_diff_stats(diff_text):
        if not diff_text:
            return 0, 0
        lines = diff_text.split('\n')
        additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        return additions, deletions
    
    additions, deletions = analyze_diff_stats(snippet)
    
    # 獲取當前時間
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 構建HTML留言 - 修復f-string問題
    body = f"""## 🤖 AI 程式碼審查報告

<table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
<tr>
<td style="background-color: {color}; color: white; padding: 8px 12px; border-radius: 6px; font-weight: bold; white-space: nowrap;">
{emoji} {label}
</td>
<td style="padding: 8px 12px;">
<strong>檔案:</strong> <code>{file_path}</code> {file_emoji} <em>{file_type}</em>
</td>
</tr>
<tr>
<td style="padding: 8px 12px; background-color: #f6f8fa;">
<strong>變更類型</strong>
</td>
<td style="padding: 8px 12px; background-color: #f6f8fa;">
{topic}
</td>
</tr>
<tr>
<td style="padding: 8px 12px;">
<strong>影響範圍</strong>
</td>
<td style="padding: 8px 12px;">
<span style="background-color: #dafbe1; color: #1a7f37; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;">+{additions}</span>
<span style="background-color: #ffebe9; color: #d1242f; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;">-{deletions}</span>
</td>
</tr>
</table>

### 📝 分析說明
{description}"""

    # 添加建議區塊
    if suggestion:
        body += f"""

### 💡 改進建議
<blockquote style="border-left: 4px solid #0969da; padding-left: 16px; margin: 16px 0; color: #656d76; background-color: #f6f8fa; padding: 12px; border-radius: 0 6px 6px 0;">
{suggestion}
</blockquote>"""

    # 添加程式碼區塊
    if snippet:
        body += f"""

### 📋 程式碼變更
<details style="border: 1px solid #d0d7de; border-radius: 6px; margin: 16px 0;">
<summary style="padding: 12px; background-color: #f6f8fa; cursor: pointer; font-weight: 600; border-radius: 6px 6px 0 0;">
🔍 點擊展開檢視程式碼差異 ({additions} 新增, {deletions} 刪除)
</summary>
<div style="padding: 16px; background-color: #0d1117;">

```diff
{snippet}
```

</div>
</details>

<div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px; margin: 12px 0;">
<strong>📖 閱讀提示:</strong><br>
• <span style="color: #1a7f37;">綠色行 (+)</span>: 新增的程式碼<br>
• <span style="color: #d1242f;">紅色行 (-)</span>: 刪除的程式碼<br>
• 白色行: 上下文程式碼
</div>"""

    # 添加工具推薦表格
    body += f"""

---

### 🛠️ 檢視工具推薦

<table style="width: 100%; border-collapse: collapse; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden;">
<thead>
<tr style="background-color: #f6f8fa;">
<th style="padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de;">工具</th>
<th style="padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de;">操作</th>
<th style="padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de;">說明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;"><strong>GitHub Web IDE</strong></td>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;"><kbd>.</kbd> 鍵</td>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;">在瀏覽器中開啟完整編輯器</td>
</tr>
<tr>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;"><strong>本地檢視</strong></td>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;"><code>git checkout pr/{PR_NUMBER}</code></td>
<td style="padding: 8px 12px; border-bottom: 1px solid #d0d7de;">切換到此PR分支</td>
</tr>
<tr>
<td style="padding: 8px 12px;"><strong>線上對比</strong></td>
<td style="padding: 8px 12px;"><a href="https://www.diffchecker.com" style="color: #0969da;">diffchecker.com</a></td>
<td style="padding: 8px 12px;">視覺化程式碼對比</td>
</tr>
</tbody>
</table>

<sub>🤖 <em>由 AI 程式碼審查助手自動生成</em> | 📅 <em>{current_time}</em></sub>"""
    
    return body

def create_svg_visual_report(comment_data):
    """生成SVG視覺化報告"""
    
    file_path = comment_data.get('file_path', 'N/A')
    topic = comment_data.get('topic', 'N/A')  
    priority = comment_data.get('priority', 'Medium')
    snippet = comment_data.get('code_snippet', '').strip()
    
    # 統計分析
    def analyze_stats(diff_text):
        if not diff_text:
            return 0, 0
        lines = diff_text.split('\n')
        additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        return additions, deletions
    
    additions, deletions = analyze_stats(snippet)
    
    # 顏色配置
    colors = {
        'High': '#d1242f',
        'Medium': '#bf8700',
        'Low': '#1a7f37'
    }
    
    color = colors.get(priority, '#bf8700')
    
    # 生成SVG - 修復XML格式問題
    svg_content = f'''<svg width="100%" height="100" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #d0d7de; border-radius: 6px; background: #f6f8fa;">
  <defs>
    <linearGradient id="priorityGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
    </linearGradient>
  </defs>
  
  <rect x="16" y="16" width="120" height="24" fill="url(#priorityGrad)" rx="12"/>
  <text x="76" y="30" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="10" font-weight="bold">
    {priority.upper()} PRIORITY
  </text>
  
  <text x="150" y="30" fill="#24292f" font-family="monospace" font-size="12" font-weight="bold">
    📁 {file_path}
  </text>
  
  <text x="16" y="55" fill="#656d76" font-family="Arial, sans-serif" font-size="11">
    🔍 {topic}
  </text>
  
  <rect x="16" y="65" width="50" height="18" fill="#dafbe1" rx="9"/>
  <text x="41" y="76" text-anchor="middle" fill="#1a7f37" font-family="Arial, sans-serif" font-size="9" font-weight="bold">
    +{additions}
  </text>
  
  <rect x="75" y="65" width="50" height="18" fill="#ffebe9" rx="9"/>
  <text x="100" y="76" text-anchor="middle" fill="#d1242f" font-family="Arial, sans-serif" font-size="9" font-weight="bold">
    -{deletions}
  </text>
  
  <circle cx="550" cy="35" r="20" fill="{color}" opacity="0.2"/>
  <text x="550" y="40" text-anchor="middle" fill="{color}" font-family="Arial, sans-serif" font-size="14">
    🤖
  </text>
</svg>'''
    
    return svg_content

def post_comment_svg_enhanced(comment_data):
    """使用SVG增強的留言格式"""
    
    svg_visual = create_svg_visual_report(comment_data)
    description = comment_data.get('description', '無說明')
    suggestion = comment_data.get('suggestion', '')
    snippet = comment_data.get('code_snippet', '').strip()
    
    body = f"""## 🤖 AI 程式碼審查報告

{svg_visual}

### 📝 詳細分析
{description}"""

    if suggestion:
        body += f"""

### 💡 改進建議
> {suggestion}"""

    if snippet:
        body += f"""

### 📋 程式碼變更
<details>
<summary><strong>點擊展開檢視程式碼差異</strong></summary>

```diff
{snippet}
```

</details>"""

    body += """

---
<sub>🤖 由 AI 程式碼審查助手自動生成</sub>"""
    
    return body

def create_gist_report(analysis_points, pr_number):
    """創建Gist HTML報告"""
    
    # 修復字符串格式問題
    html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR """ + str(pr_number) + """ 程式碼審查報告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
               background: #f6f8fa; color: #24292f; padding: 20px; line-height: 1.6; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; 
                  box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; 
                  border: 1px solid #d0d7de; }
        .analysis-card { background: white; border: 1px solid #d0d7de; border-radius: 8px; 
                         margin-bottom: 16px; overflow: hidden; }
        .card-header { background: #f6f8fa; padding: 16px; cursor: pointer; 
                       border-bottom: 1px solid #d0d7de; }
        .card-content { padding: 16px; display: none; }
        .card-content.active { display: block; }
        .priority-high { border-left: 4px solid #d1242f; }
        .priority-medium { border-left: 4px solid #bf8700; }
        .priority-low { border-left: 4px solid #1a7f37; }
        .code-block { background: #f6f8fa; border: 1px solid #d0d7de; 
                      border-radius: 6px; padding: 16px; font-family: monospace; 
                      font-size: 14px; overflow-x: auto; }
        .stats { display: flex; gap: 8px; margin: 8px 0; }
        .stat-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .additions { background: #dafbe1; color: #1a7f37; }
        .deletions { background: #ffebe9; color: #d1242f; }
        .toggle-btn { background: #0969da; color: white; border: none; 
                     padding: 8px 16px; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI 程式碼審查完整報告</h1>
            <p><strong>Pull Request #""" + str(pr_number) + """</strong> | 共 """ + str(len(analysis_points)) + """ 個分析項目</p>
            <button class="toggle-btn" onclick="toggleAll()">全部展開/收合</button>
        </div>
"""
    
    for i, point in enumerate(analysis_points):
        priority_class = f"priority-{point.get('priority', 'medium').lower()}"
        
        # 統計分析
        snippet = point.get('code_snippet', '')
        additions = deletions = 0
        if snippet:
            lines = snippet.split('\n')
            additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        # 優先級顏色
        priority_color = '#d1242f' if point.get('priority') == 'High' else '#bf8700' if point.get('priority') == 'Medium' else '#1a7f37'
        
        html_content += f"""
        <div class="analysis-card {priority_class}">
            <div class="card-header" onclick="toggleCard({i})">
                <h3>📁 {point.get('file_path', 'N/A')}</h3>
                <p><strong>{point.get('topic', 'N/A')}</strong> - 
                   <span style="color: {priority_color};">
                   {point.get('priority', 'Medium')} Priority</span></p>
                <div class="stats">
                    <span class="stat-badge additions">+{additions}</span>
                    <span class="stat-badge deletions">-{deletions}</span>
                </div>
            </div>
            <div class="card-content" id="card-{i}">
                <h4>📝 分析說明</h4>
                <p>{point.get('description', '')}</p>"""
        
        if point.get('suggestion'):
            html_content += f"""<h4>💡 改進建議</h4><blockquote style="border-left: 4px solid #0969da; padding-left: 12px; color: #656d76;">{point.get('suggestion', '')}</blockquote>"""
        
        if point.get('code_snippet'):
            html_content += f"""<h4>📋 程式碼變更</h4><div class="code-block"><pre>{point.get('code_snippet', '')}</pre></div>"""
        
        html_content += """
            </div>
        </div>
        """
    
    html_content += """
    </div>
    <script>
        let allExpanded = false;
        
        function toggleCard(index) {
            const content = document.getElementById('card-' + index);
            content.classList.toggle('active');
        }
        
        function toggleAll() {
            const contents = document.querySelectorAll('.card-content');
            allExpanded = !allExpanded;
            contents.forEach(content => {
                if (allExpanded) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        }
        
        // 預設展開第一個
        if (document.getElementById('card-0')) {
            document.getElementById('card-0').classList.add('active');
        }
    </script>
</body>
</html>"""
    
    # 創建Gist
    gist_payload = {
        "description": f"PR {pr_number} AI 程式碼審查完整報告",
        "public": True,
        "files": {
            f"pr-{pr_number}-analysis.html": {
                "content": html_content
            }
        }
    }
    
    try:
        response = requests.post("https://api.github.com/gists", 
                               json=gist_payload, headers=GITHUB_HEADERS)
        if response.status_code == 201:
            gist_data = response.json()
            return {
                'gist_url': gist_data['html_url'],
                'raw_url': gist_data['files'][f"pr-{pr_number}-analysis.html"]['raw_url'],
                'preview_url': f"https://htmlpreview.github.io/?{gist_data['files'][f'pr-{pr_number}-analysis.html']['raw_url']}"
            }
    except Exception as e:
        print(f"創建Gist失敗: {e}")
        return None

def post_comment_with_html_strategy(comment_data, strategy="github_native"):
    """根據策略選擇HTML留言格式"""
    
    if strategy == "github_native":
        body = post_comment_github_native_html(comment_data)
    elif strategy == "svg_enhanced":
        body = post_comment_svg_enhanced(comment_data)
    else:
        # 回退到基本格式
        body = post_comment_github_native_html(comment_data)
    
    # 發送留言
    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    response = requests.post(url, json={'body': body}, headers=GITHUB_HEADERS)
    
    try:
        response.raise_for_status()
        print(f"✅ 成功發佈HTML留言 ({strategy}): {comment_data.get('topic', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 發佈失敗: {e}")
        return False

def post_gist_summary(analysis_points):
    """發佈Gist完整報告的摘要留言"""
    
    gist_info = create_gist_report(analysis_points, PR_NUMBER)
    
    if gist_info:
        # 統計分析
        high_count = sum(1 for p in analysis_points if p.get('priority') == 'High')
        medium_count = sum(1 for p in analysis_points if p.get('priority') == 'Medium')
        low_count = sum(1 for p in analysis_points if p.get('priority') == 'Low')
        
        summary_body = f"""## 🤖 AI 程式碼審查完整報告

### 📊 分析摘要
- 🔍 **分析檔案**: {len(analysis_points)} 個
- 🔴 **高優先級**: {high_count} 個
- 🟡 **中優先級**: {medium_count} 個  
- 🟢 **低優先級**: {low_count} 個

### 🌐 完整互動式報告

<table style="width: 100%; border-collapse: collapse; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden;">
<thead>
<tr style="background-color: #f6f8fa;">
<th style="padding: 12px; text-align: left;">報告類型</th>
<th style="padding: 12px; text-align: left;">連結</th>
<th style="padding: 12px; text-align: left;">說明</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 12px; border-top: 1px solid #d0d7de;"><strong>🔗 原始Gist</strong></td>
<td style="padding: 12px; border-top: 1px solid #d0d7de;"><a href="{gist_info['gist_url']}" style="color: #0969da;">查看Gist</a></td>
<td style="padding: 12px; border-top: 1px solid #d0d7de;">可編輯的原始檔案</td>
</tr>
<tr>
<td style="padding: 12px; border-top: 1px solid #d0d7de;"><strong>🌐 HTML預覽</strong></td>
<td style="padding: 12px; border-top: 1px solid #d0d7de;"><a href="{gist_info['preview_url']}" style="color: #0969da;">線上預覽</a></td>
<td style="padding: 12px; border-top: 1px solid #d0d7de;">完整互動式報告</td>
</tr>
</tbody>
</table>

### 🚀 報告特色
- ✅ **互動式檢視**: 可展開/收合每個分析項目
- ✅ **語法高亮**: 程式碼差異清晰顯示
- ✅ **統計圖表**: 變更統計一目了然
- ✅ **響應式設計**: 手機和桌面都完美支援

---
<sub>🤖 完整報告包含所有分析細節，建議點擊上方連結查看</sub>"""
        
        # 發送摘要留言
        url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
        response = requests.post(url, json={'body': summary_body}, headers=GITHUB_HEADERS)
        
        try:
            response.raise_for_status()
            print(f"✅ 成功發佈Gist完整報告摘要")
            return True
        except Exception as e:
            print(f"❌ 發佈Gist摘要失敗: {e}")
            return False
    
    return False

# 主程式整合
if __name__ == "__main__":
    try:
        print("🚀 開始分析 Pull Request...")
        print("=" * 50)
        
        # 獲取diff和分析
        diff = get_pr_diff()
        analysis_points = analyze_diff_with_gemini(diff)
        
        if analysis_points:
            print(f"分析完成！使用HTML策略: {HTML_STRATEGY}")
            
            if HTML_STRATEGY == "gist_report":
                # 使用Gist完整報告
                post_gist_summary(analysis_points)
            else:
                # 使用選定的HTML策略發佈每個分析點
                for point in analysis_points:
                    post_comment_with_html_strategy(point, HTML_STRATEGY)
        
        print("✅ 所有HTML增強留言已發佈！")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
