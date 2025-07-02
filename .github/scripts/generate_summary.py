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
    
    # 解析diff內容
    def parse_diff_lines(diff_text):
        lines = diff_text.split('\n')
        parsed = []
        line_num = 1
        
        for line in lines:
            line_type = 'context'
            if line.startswith('@@'):
                line_type = 'hunk'
            elif line.startswith('+'):
                line_type = 'added'
            elif line.startswith('-'):
                line_type = 'removed'
            
            parsed.append({
                'content': line,
                'type': line_type,
                'number': line_num
            })
            line_num += 1
        
        return parsed
    
    # 簡單的語法高亮
    def highlight_syntax(code):
        import re
        # 關鍵字高亮
        keywords = ['import', 'export', 'const', 'let', 'var', 'function', 'class', 
                   'if', 'else', 'for', 'while', 'return', 'async', 'await', 'def', 
                   'class', 'from', 'import', 'try', 'except', 'finally']
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            code = re.sub(pattern, f'<span style="color: #ff7b72;">{keyword}</span>', code)
        
        # 字串高亮
        code = re.sub(r'(["\'])([^"\']*)\1', r'<span style="color: #a5d6ff;">\1\2\1</span>', code)
        
        # 註解高亮
        code = re.sub(r'(//.*?$|#.*?$)', r'<span style="color: #8b949e;">\1</span>', code, flags=re.MULTILINE)
        
        return code
    
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
    
    # 添加互動式樹狀檢視選項
    if snippet:
        body += f"""

### 🌳 進階檢視選項
如需更詳細的程式碼審查，建議使用以下工具：
- **線上Diff檢視器**: 可貼上程式碼到 [diffchecker.com](https://www.diffchecker.com)
- **IDE整合**: 在您的開發環境中檢視完整的檔案脈絡
- **GitHub Web IDE**: 按下 `.` 鍵開啟 GitHub 網頁版編輯器"""
    
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

# 替代方案：生成完整的HTML報告
def generate_pr_analysis_report(all_analysis_points):
    """生成完整的PR分析HTML報告"""
    
    html_report = '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PR 分析報告</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                   background: #f6f8fa; margin: 0; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; 
                     box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .file-card { background: white; border-radius: 8px; 
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; overflow: hidden; }
            .file-header { background: #f1f3f4; padding: 12px 16px; 
                          border-bottom: 1px solid #e1e4e8; cursor: pointer; }
            .file-content { padding: 16px; display: none; }
            .priority-high { border-left: 4px solid #d73a49; }
            .priority-medium { border-left: 4px solid #f66a0a; }
            .priority-low { border-left: 4px solid #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI 程式碼審查報告</h1>
                <p>自動分析結果 - 共發現 ''' + str(len(all_analysis_points)) + ''' 個關注點</p>
            </div>
    '''
    
    for i, point in enumerate(all_analysis_points):
        priority_class = f"priority-{point.get('priority', 'medium').lower()}"
        html_report += f'''
            <div class="file-card {priority_class}">
                <div class="file-header" onclick="toggleContent({i})">
                    <h3>📁 {point.get('file_path', 'N/A')}</h3>
                    <p><strong>{point.get('topic', 'N/A')}</strong> - {point.get('priority', 'Medium')} Priority</p>
                </div>
                <div class="file-content" id="content-{i}">
                    <p>{point.get('description', '')}</p>
                    {f"<blockquote><strong>建議:</strong> {point.get('suggestion', '')}</blockquote>" if point.get('suggestion') else ""}
                    {generate_enhanced_diff_html(point.get('code_snippet', ''), point.get('file_path', '')) if point.get('code_snippet') else ""}
                </div>
            </div>
        '''
    
    html_report += '''
        </div>
        <script>
            function toggleContent(index) {
                const content = document.getElementById('content-' + index);
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    '''
    
    return html_report

# 在主程式中的使用方式
def main_enhanced():
    """主程式的增強版本"""
    try:
        print("🚀 開始分析 Pull Request...")
        
        # 獲取diff內容
        diff = get_pr_diff()
        
        # AI分析
        analysis_points = analyze_diff_with_gemini(diff)
        
        if analysis_points:
            print(f"✅ 分析完成！準備發佈 {len(analysis_points)} 個增強版分析結果...")
            
            # 選擇發佈方式
            USE_ENHANCED_COMMENTS = True  # 設定為True使用增強版留言
            
            if USE_ENHANCED_COMMENTS:
                # 使用增強版留言
                for i, point in enumerate(analysis_points, 1):
                    print(f"發佈第 {i} 個增強版分析要點...")
                    post_comment_enhanced(point)
            else:
                # 或者生成完整的HTML報告並作為單一留言發佈
                html_report = generate_pr_analysis_report(analysis_points)
                
                # 將HTML報告作為留言發佈（GitHub支援HTML）
                summary_comment = {
                    "file_path": "Complete Analysis Report",
                    "topic": "完整分析報告",
                    "description": "點擊下方展開檢視完整的程式碼審查報告",
                    "priority": "High",
                    "suggestion": "",
                    "code_snippet": ""  # HTML報告會在description中
                }
                
                post_comment({
                    **summary_comment,
                    "description": f"{summary_comment['description']}\n\n<details><summary>📊 完整分析報告</summary>\n\n{html_report}\n\n</details>"
                })
        
        print("✅ 所有增強版分析結果已發佈！")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    main_enhanced()
