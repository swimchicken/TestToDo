import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

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

def get_pr_diff():
    """取得 Pull Request 的完整 diff 內容"""
    try:
        pr_url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
        pr_response = requests.get(pr_url, headers=GITHUB_HEADERS)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        
        print(f"PR 標題: {pr_data.get('title', 'N/A')}")
        
        files = get_pr_files()
        print(f"實際獲取到 {len(files)} 個變更文件")
        
        if not files:
            return "No files changed in this PR."
        
        full_diff = f"Pull Request: {pr_data.get('title', '')}\n"
        full_diff += f"Files changed: {len(files)}\n\n"
        
        for file_data in files:
            filename = file_data['filename']
            status = file_data['status']
            additions = file_data.get('additions', 0)
            deletions = file_data.get('deletions', 0)
            
            print(f"處理文件: {filename} (狀態: {status}, +{additions}/-{deletions})")
            
            file_diff = f"\n{'='*50}\n"
            file_diff += f"File: {filename}\n"
            file_diff += f"Status: {status}\n"
            file_diff += f"Changes: +{additions}/-{deletions}\n"
            file_diff += f"{'='*50}\n"
            
            if 'patch' in file_data and file_data['patch']:
                file_diff += file_data['patch']
            else:
                file_diff += f"(No patch data available for {filename})"
            
            full_diff += file_diff + "\n"
        
        if len(full_diff) > 25000:
            print(f"⚠️  Diff 內容過長，進行截斷...")
            return full_diff[:25000] + "\n\n⚠️ 內容已截斷"
        
        return full_diff
        
    except Exception as e:
        print(f"獲取 PR diff 時發生錯誤: {e}")
        return f"Error fetching PR diff: {str(e)}"

def analyze_diff_with_gemini(diff_text):
    """使用 Gemini API 分析 diff - 增強版，包含行號和建議修復"""
    if not diff_text.strip():
        return []

    model = genai.GenerativeModel(GEMINI_MODEL)
    
    prompt_template = """
    您是一位專業的 GitHub 程式碼審查專家。請分析下方的 Pull Request diff 內容，提供具體的程式碼審查建議。

    **重要要求：**
    1. 必須回傳有效的 JSON 陣列格式
    2. 專注於可操作的具體建議
    3. 提供修復後的程式碼範例
    4. 評估安全性、效能、程式碼品質問題

    **回應格式：**每個物件包含以下欄位：
    - `file_path`: 檔案路徑
    - `line_number`: 問題所在行號（如果可識別）
    - `severity`: 嚴重程度（"Critical", "Warning", "Info"）
    - `category`: 問題類別（"Security", "Performance", "Code Quality", "Bug Risk"等）
    - `title`: 問題標題（簡短描述）
    - `description`: 詳細問題說明
    - `suggestion`: 具體改進建議
    - `fixed_code`: 修復後的程式碼範例（如果適用）
    - `original_code`: 原始有問題的程式碼

    範例輸出：
    [
        {
            "file_path": "src/services/apiService.js",
            "line_number": 5,
            "severity": "Critical",
            "category": "Security",
            "title": "API密鑰硬編碼風險",
            "description": "直接在程式碼中硬編碼API密鑰會造成安全風險，任何能訪問程式碼的人都能看到密鑰。",
            "suggestion": "將API密鑰移至環境變數中，使用process.env.API_KEY讀取。",
            "fixed_code": "const apiKey = process.env.REACT_APP_API_KEY;",
            "original_code": "const apiKey = 'sk-1234567890abcdef';"
        }
    ]

    請用繁體中文分析以下 diff：

    ```diff
    __DIFF_PLACEHOLDER__
    ```
    """
    
    prompt = prompt_template.replace("__DIFF_PLACEHOLDER__", diff_text)
    
    try:
        print("正在呼叫 Gemini API...")
        response = model.generate_content(prompt)
        
        if not response.text:
            return []
        
        cleaned_text = response.text.strip()
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        
        try:
            analysis_results = json.loads(cleaned_text)
            if isinstance(analysis_results, list):
                print(f"成功解析 {len(analysis_results)} 個分析要點")
                return analysis_results
            else:
                return []
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗: {e}")
            return []
            
    except Exception as e:
        print(f"API 呼叫錯誤: {e}")
        return []

def create_github_style_comment(analysis_data):
    """創建類似GitHub原生體驗的留言"""
    
    file_path = analysis_data.get('file_path', 'N/A')
    line_number = analysis_data.get('line_number', '')
    severity = analysis_data.get('severity', 'Info')
    category = analysis_data.get('category', 'Code Quality')
    title = analysis_data.get('title', '程式碼建議')
    description = analysis_data.get('description', '')
    suggestion = analysis_data.get('suggestion', '')
    fixed_code = analysis_data.get('fixed_code', '')
    original_code = analysis_data.get('original_code', '')
    
    # 嚴重程度樣式
    severity_config = {
        'Critical': ('#d1242f', '🔴', 'Critical'),
        'Warning': ('#bf8700', '🟡', 'Warning'),
        'Info': ('#0969da', '🔵', 'Info')
    }
    
    color, emoji, label = severity_config.get(severity, ('#0969da', '🔵', 'Info'))
    
    # 類別圖示
    category_icons = {
        'Security': '🔒', 'Performance': '⚡', 'Code Quality': '✨',
        'Bug Risk': '🐛', 'Maintainability': '🔧', 'Best Practice': '💡'
    }
    
    category_icon = category_icons.get(category, '📋')
    
    # 構建留言內容
    body = f"""## {emoji} {title}

<table style="width: 100%; border: none; margin-bottom: 16px;">
<tr>
<td style="background-color: {color}; color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; white-space: nowrap; border: none;">
{label}
</td>
<td style="padding: 6px 12px; border: none;">
{category_icon} <strong>{category}</strong>
</td>
<td style="padding: 6px 12px; text-align: right; border: none;">
📁 <code>{file_path}</code>{f' :line_number: {line_number}' if line_number else ''}
</td>
</tr>
</table>

### 🔍 問題說明
{description}

### 💡 建議修改
{suggestion}"""

    # 添加程式碼對比
    if original_code and fixed_code:
        body += f"""

### 📋 程式碼修改建議

<table style="width: 100%; border-collapse: collapse; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden; margin: 16px 0;">
<thead>
<tr style="background-color: #f6f8fa;">
<th style="padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de; width: 50%;">❌ 修改前</th>
<th style="padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de; width: 50%;">✅ 修改後</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 12px; border-right: 1px solid #d0d7de; background-color: #ffebe9; vertical-align: top;">

```javascript
{original_code}
```

</td>
<td style="padding: 12px; background-color: #dafbe1; vertical-align: top;">

```javascript
{fixed_code}
```

</td>
</tr>
</tbody>
</table>"""

    elif original_code or fixed_code:
        # 如果只有其中一個
        code_to_show = fixed_code if fixed_code else original_code
        code_label = "建議程式碼" if fixed_code else "相關程式碼"
        
        body += f"""

### 📝 {code_label}

```javascript
{code_to_show}
```"""

    # 添加底部標籤（移除了"如何修改"部分）
    body += f"""

---

<sub>🤖 <em>由 AI 程式碼審查助手自動生成</em> | {category_icon} <em>{category}</em> | 📅 <em>{datetime.now().strftime("%Y-%m-%d %H:%M")}</em></sub>"""
    
    return body

def create_summary_comment(analysis_results):
    """創建摘要留言"""
    
    if not analysis_results:
        return None
    
    # 統計分析
    critical_count = sum(1 for item in analysis_results if item.get('severity') == 'Critical')
    warning_count = sum(1 for item in analysis_results if item.get('severity') == 'Warning')
    info_count = sum(1 for item in analysis_results if item.get('severity') == 'Info')
    
    # 按類別統計
    categories = {}
    for item in analysis_results:
        cat = item.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1
    
    body = f"""## 🤖 AI 程式碼審查摘要報告

### 📊 總體統計

<table style="width: 100%; border-collapse: collapse; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden;">
<thead>
<tr style="background-color: #f6f8fa;">
<th style="padding: 12px; text-align: center; border-bottom: 1px solid #d0d7de;">🔴 Critical</th>
<th style="padding: 12px; text-align: center; border-bottom: 1px solid #d0d7de;">🟡 Warning</th>
<th style="padding: 12px; text-align: center; border-bottom: 1px solid #d0d7de;">🔵 Info</th>
<th style="padding: 12px; text-align: center; border-bottom: 1px solid #d0d7de;">📋 總計</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 12px; text-align: center; background-color: {('#ffebe9' if critical_count > 0 else '#f6f8fa')};">
<strong style="color: #d1242f;">{critical_count}</strong>
</td>
<td style="padding: 12px; text-align: center; background-color: {('#fff3cd' if warning_count > 0 else '#f6f8fa')};">
<strong style="color: #bf8700;">{warning_count}</strong>
</td>
<td style="padding: 12px; text-align: center; background-color: {('#e7f3ff' if info_count > 0 else '#f6f8fa')};">
<strong style="color: #0969da;">{info_count}</strong>
</td>
<td style="padding: 12px; text-align: center;">
<strong>{len(analysis_results)}</strong>
</td>
</tr>
</tbody>
</table>

### 🏷️ 問題分類"""

    # 添加分類統計
    for category, count in categories.items():
        category_icon = {
            'Security': '🔒', 'Performance': '⚡', 'Code Quality': '✨',
            'Bug Risk': '🐛', 'Maintainability': '🔧', 'Best Practice': '💡'
        }.get(category, '📋')
        
        body += f"""
- {category_icon} **{category}**: {count} 個問題"""

    # 添加快速導航
    body += f"""

### 🔍 詳細問題列表"""

    for i, item in enumerate(analysis_results, 1):
        severity_emoji = {'Critical': '🔴', 'Warning': '🟡', 'Info': '🔵'}.get(item.get('severity'), '🔵')
        category_icon = {
            'Security': '🔒', 'Performance': '⚡', 'Code Quality': '✨',
            'Bug Risk': '🐛', 'Maintainability': '🔧', 'Best Practice': '💡'
        }.get(item.get('category'), '📋')
        
        body += f"""
{i}. {severity_emoji} **{item.get('title', 'N/A')}** {category_icon}  
   📁 `{item.get('file_path', 'N/A')}`{f" :line_number: {item.get('line_number')}" if item.get('line_number') else ""}"""

    body += f"""

---

<sub>🤖 <em>完整的程式碼審查助手</em> | 📅 <em>{datetime.now().strftime("%Y-%m-%d %H:%M")}</em></sub>"""
    
    return body

def post_comment(body):
    """發佈留言到 PR"""
    url = f"{GITHUB_API_URL}/repos/{REPO}/issues/{PR_NUMBER}/comments"
    response = requests.post(url, json={'body': body}, headers=GITHUB_HEADERS)
    
    try:
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 發佈留言失敗: {e}")
        return False

def post_review_comment(file_path, line_number, body):
    """發佈程式碼行級別的審查留言（如果可能的話）"""
    
    # 嘗試發佈 review comment（行級別）
    try:
        # 首先獲取PR的SHA
        pr_url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}"
        pr_response = requests.get(pr_url, headers=GITHUB_HEADERS)
        pr_data = pr_response.json()
        
        sha = pr_data['head']['sha']
        
        review_payload = {
            "body": "AI 程式碼審查",
            "event": "COMMENT",
            "comments": [
                {
                    "path": file_path,
                    "line": line_number,
                    "body": body
                }
            ]
        }
        
        review_url = f"{GITHUB_API_URL}/repos/{REPO}/pulls/{PR_NUMBER}/reviews"
        review_response = requests.post(review_url, json=review_payload, headers=GITHUB_HEADERS)
        
        if review_response.status_code == 200:
            print(f"✅ 成功發佈行級別留言: {file_path}:{line_number}")
            return True
        else:
            print(f"⚠️  行級別留言失敗，改用一般留言")
            return False
            
    except Exception as e:
        print(f"⚠️  無法發佈行級別留言: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🚀 開始進行 GitHub 風格的程式碼審查...")
        print("=" * 50)
        
        # 獲取diff和分析
        diff = get_pr_diff()
        analysis_results = analyze_diff_with_gemini(diff)
        
        if analysis_results:
            print(f"✅ 分析完成！發現 {len(analysis_results)} 個問題")
            
            # 先發佈摘要留言
            summary_body = create_summary_comment(analysis_results)
            if summary_body:
                post_comment(summary_body)
                print("✅ 摘要報告已發佈")
            
            # 發佈每個詳細問題
            success_count = 0
            for i, analysis in enumerate(analysis_results, 1):
                print(f"\n發佈第 {i} 個問題: {analysis.get('title', 'N/A')}")
                
                comment_body = create_github_style_comment(analysis)
                
                # 嘗試行級別留言，失敗則用一般留言
                line_num = analysis.get('line_number')
                file_path = analysis.get('file_path')
                
                if line_num and file_path:
                    if not post_review_comment(file_path, line_num, comment_body):
                        # 行級別失敗，使用一般留言
                        if post_comment(comment_body):
                            success_count += 1
                    else:
                        success_count += 1
                else:
                    # 沒有行號，直接用一般留言
                    if post_comment(comment_body):
                        success_count += 1
            
            print("\n" + "=" * 50)
            print(f"✅ GitHub風格程式碼審查完成！成功發佈 {success_count}/{len(analysis_results)} 個問題")
        else:
            print("ℹ️  沒有發現需要審查的問題")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
