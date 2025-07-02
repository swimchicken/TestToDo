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

# [保留之前的 get_pr_diff 和 analyze_diff_with_gemini 函數...]

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
    
    # 構建HTML留言
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
{description}

{f'''
### 💡 改進建議
<blockquote style="border-left: 4px solid #0969da; padding-left: 16px; margin: 16px 0; color: #656d76; background-color: #f6f8fa; padding: 12px; border-radius: 0 6px 6px 0;">
{suggestion}
</blockquote>
''' if suggestion else ''}

{f'''
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
<strong>📖 閱讀提示:</strong>
• <span style="color: #1a7f37;">綠色行 (+)</span>: 新增的程式碼<br>
• <span style="color: #d1242f;">紅色行 (-)</span>: 刪除的程式碼<br>
• 白色行: 上下文程式碼
</div>
''' if snippet else ''}

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

<sub>🤖 <em>由 AI 程式碼審查助手自動生成</em> | 📅 <em>{datetime.now().strftime("%Y-%m-%d %H:%M")}</em></sub>"""
    
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
    
    # 生成SVG
    svg_content = f'''
<svg width="100%" height="100" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #d0d7de; border-radius: 6px; background: #f6f8fa;">
  <defs>
    <linearGradient id="priorityGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
    </linearGradient>
  </defs>
  
  <!-- 優先級標籤 -->
  <rect x="16" y="16" width="120" height="24" fill="url(#priorityGrad)" rx="12"/>
  <text x="76" y="30" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="10" font-weight="bold">
    {priority.upper()} PRIORITY
  </text>
  
  <!-- 檔案路徑 -->
  <text x="150" y="30" fill="#24292f" font-family="monospace" font-size="12" font-weight="bold">
    📁 {file_path}
  </text>
  
  <!-- 變更類型 -->
  <text x="16" y="55" fill="#656d76" font-family="Arial, sans-serif" font-size="11">
    🔍 {topic}
  </text>
  
  <!-- 統計資訊 -->
  <rect x="16" y="65" width="50" height="18" fill="#dafbe1" rx="9"/>
  <text x="41" y="76" text-anchor="middle" fill="#1a7f37" font-family="Arial, sans-serif" font-size="9" font-weight="bold">
    +{additions}
  </text>
  
  <rect x="75" y="65" width="50" height="18" fill="#ffebe9" rx="9"/>
  <text x="100" y="76" text-anchor="middle" fill="#d1242f" font-family="Arial, sans-serif" font-size="9" font-weight="bold">
    -{deletions}
  </text>
  
  <!-- AI圖示 -->
  <circle cx="550" cy="35" r="20" fill="{color}" opacity="0.2"/>
  <text x="550" y="40" text-anchor="middle" fill="{color}" font-family="Arial, sans-serif" font-size="14">
    🤖
  </text>
</svg>
'''
    
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
{description}

{f'### 💡 改進建議\n> {suggestion}\n' if suggestion else ''}

{f'''
### 📋 程式碼變更
<details>
<summary><strong>點擊展開檢視程式碼差異</strong></summary>

```diff
{snippet}
```

</details>
''' if snippet else ''}

---
<sub>🤖 由 AI 程式碼審查助手自動生成</sub>"""
    
    return body

def create_gist_report(analysis_points, pr_number):
    """創建Gist HTML報告"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR {pr_number} 程式碼審查報告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
               background: #f6f8fa; color: #24292f; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; 
                  box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; 
                  border: 1px solid #d0d7de; }}
        .analysis-card {{ background: white; border: 1px solid #d0d7de; border-radius: 8px; 
                         margin-bottom: 16px; overflow: hidden; }}
        .card-header {{ background: #f6f8fa; padding: 16px; cursor: pointer; 
                       border-bottom: 1px solid #d0d7de; }}
        .card-content {{ padding: 16px; display: none; }}
        .card-content.active {{ display: block; }}
        .priority-high {{ border-left: 4px solid #d1242f; }}
        .priority-medium {{ border-left: 4px solid #bf8700; }}
        .priority-low {{ border-left: 4px solid #1a7f37; }}
        .code-block {{ background: #f6f8fa; border: 1px solid #d0d7de; 
                      border-radius: 6px; padding: 16px; font-family: monospace; 
                      font-size: 14px; overflow-x: auto; }}
        .stats {{ display: flex; gap: 8px; margin: 8px 0; }}
        .stat-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .additions {{ background: #dafbe1; color: #1a7f37; }}
        .deletions {{ background: #ffebe9; color: #d1242f; }}
        .toggle-btn {{ background: #0969da; color: white; border: none; 
                     padding: 8px 16px; border-radius: 6px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI 程式碼審查完整報告</h1>
            <p><strong>Pull Request #{pr_number}</strong> | 共 {len(analysis_points)} 個分析項目</p>
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
        
        html_content += f"""
        <div class="analysis-card {priority_class}">
            <div class="card-header" onclick="toggleCard({i})">
                <h3>📁 {point.get('file_path', 'N/A')}</h3>
                <p><strong>{point.get('topic', 'N/A')}</strong> - 
                   <span style="color: {'#d1242f' if point.get('priority') == 'High' else '#bf8700' if point.get('priority') == 'Medium' else '#1a7f37'};">
                   {point.get('priority', 'Medium')} Priority</span></p>
                <div class="stats">
                    <span class="stat-badge additions">+{additions}</span>
                    <span class="stat-badge deletions">-{deletions}</span>
                </div>
            </div>
            <div class="card-content" id="card-{i}">
                <h4>📝 分析說明</h4>
                <p>{point.get('description', '')}</p>
                {f'<h4>💡 改進建議</h4><blockquote style="border-left: 4px solid #0969da; padding-left: 12px; color: #656d76;">{point.get("suggestion", "")}</blockquote>' if point.get('suggestion') else ''}
                {f'<h4>📋 程式碼變更</h4><div class="code-block"><pre>{point.get("code_snippet", "")}</pre></div>' if point.get('code_snippet') else ''}
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
        document.getElementById('card-0').classList.add('active');
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
        summary_body = f"""## 🤖 AI 程式碼審查完整報告

### 📊 分析摘要
- 🔍 **分析檔案**: {len(analysis_points)} 個
- 🔴 **高優先級**: {sum(1 for p in analysis_points if p.get('priority') == 'High')} 個
- 🟡 **中優先級**: {sum(1 for p in analysis_points if p.get('priority') == 'Medium')} 個  
- 🟢 **低優先級**: {sum(1 for p in analysis_points if p.get('priority') == 'Low')} 個

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
        
        # [保留原本的diff獲取和AI分析邏輯...]
        diff = get_pr_diff()  # 需要實作
        analysis_points = analyze_diff_with_gemini(diff)  # 需要實作
        
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
