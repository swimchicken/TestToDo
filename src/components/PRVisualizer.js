import React, { useState } from 'react';
import { analyzeDiff, generatePRSummary } from '../services/geminiService';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import PRCommentGUI from './PRCommentGUI';

const PRVisualizer = () => {
  const [diffContent, setDiffContent] = useState('');
  const [prTitle, setPrTitle] = useState('');
  const [prDescription, setPrDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [showCommentGUI, setShowCommentGUI] = useState(false);

  // 示例 PR 資料
  const samplePR = {
    title: "新增使用者認證功能",
    description: "實作 JWT 認證機制，包含登入、註冊和權限管理功能",
    diff: `diff --git a/src/auth/AuthContext.js b/src/auth/AuthContext.js
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/AuthContext.js
@@ -0,0 +1,45 @@
+import React, { createContext, useContext, useState, useEffect } from 'react';
+
+const AuthContext = createContext();
+
+export const useAuth = () => {
+  const context = useContext(AuthContext);
+  if (!context) {
+    throw new Error('useAuth must be used within an AuthProvider');
+  }
+  return context;
+};
+
+export const AuthProvider = ({ children }) => {
+  const [user, setUser] = useState(null);
+  const [loading, setLoading] = useState(true);
+
+  const login = async (email, password) => {
+    // 實作登入邏輯
+    try {
+      const response = await fetch('/api/auth/login', {
+        method: 'POST',
+        headers: { 'Content-Type': 'application/json' },
+        body: JSON.stringify({ email, password })
+      });
+      
+      if (response.ok) {
+        const userData = await response.json();
+        setUser(userData);
+        return { success: true };
+      }
+    } catch (error) {
+      console.error('Login error:', error);
+      return { success: false, error: error.message };
+    }
+  };
+
+  const logout = () => {
+    setUser(null);
+    localStorage.removeItem('token');
+  };
+
+  return (
+    <AuthContext.Provider value={{ user, login, logout, loading }}>
+      {children}
+    </AuthContext.Provider>
+  );
+};
diff --git a/src/components/Login.js b/src/components/Login.js
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/src/components/Login.js
@@ -0,0 +1,35 @@
+import React, { useState } from 'react';
+import { useAuth } from '../auth/AuthContext';
+
+const Login = () => {
+  const [email, setEmail] = useState('');
+  const [password, setPassword] = useState('');
+  const { login } = useAuth();
+
+  const handleSubmit = async (e) => {
+    e.preventDefault();
+    const result = await login(email, password);
+    if (result.success) {
+      // 導向到主頁面
+    }
+  };
+
+  return (
+    <form onSubmit={handleSubmit}>
+      <input
+        type="email"
+        value={email}
+        onChange={(e) => setEmail(e.target.value)}
+        placeholder="電子郵件"
+        required
+      />
+      <input
+        type="password"
+        value={password}
+        onChange={(e) => setPassword(e.target.value)}
+        placeholder="密碼"
+        required
+      />
+      <button type="submit">登入</button>
+    </form>
+  );
+};
+
+export default Login;`
  };

  const loadSamplePR = () => {
    setPrTitle(samplePR.title);
    setPrDescription(samplePR.description);
    setDiffContent(samplePR.diff);
  };

  const handleAnalyzePR = async () => {
    if (!diffContent.trim() || !prTitle.trim()) {
      setError('請填寫 PR 標題和 diff 內容');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const result = await analyzeDiff(diffContent);
      const summary = await generatePRSummary(prTitle, prDescription, result);
      
      setAnalysisResult({
        analysis: result,
        summary: summary
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleShowCommentGUI = () => {
    if (!diffContent || !prTitle) {
      setError('請先填寫 PR 資訊和 diff 內容');
      return;
    }
    setShowCommentGUI(true);
  };

  return (
    <div style={{
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'Inter, sans-serif'
    }}>
      <h1 style={{ 
        textAlign: 'center', 
        color: '#333',
        marginBottom: '30px'
      }}>
        🔍 PR 視覺化分析器
      </h1>

      {/* PR 資訊輸入 */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '20px',
        marginBottom: '30px'
      }}>
        {/* 左側：PR 基本資訊 */}
        <div>
          <h2>📋 PR 基本資訊</h2>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              PR 標題
            </label>
            <input
              type="text"
              value={prTitle}
              onChange={(e) => setPrTitle(e.target.value)}
              placeholder="請輸入 PR 標題..."
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '16px'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              PR 描述
            </label>
            <textarea
              value={prDescription}
              onChange={(e) => setPrDescription(e.target.value)}
              placeholder="請描述這個 PR 的目的和變更..."
              style={{
                width: '100%',
                height: '100px',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={loadSamplePR}
              style={{
                padding: '10px 20px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              📝 載入示例 PR
            </button>
            
            <button 
              onClick={handleShowCommentGUI}
              style={{
                padding: '10px 20px',
                backgroundColor: '#17a2b8',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              💬 預覽評論 GUI
            </button>
          </div>
        </div>

        {/* 右側：快速統計 */}
        <div>
          <h2>📊 快速統計</h2>
          <div style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #dee2e6'
          }}>
            <div style={{ marginBottom: '15px' }}>
              <strong>檔案變更數：</strong>
              <span style={{ color: '#007bff' }}>
                {diffContent ? diffContent.split('diff --git').length - 1 : 0}
              </span>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <strong>新增行數：</strong>
              <span style={{ color: '#28a745' }}>
                {diffContent ? (diffContent.match(/^\+/gm) || []).length : 0}
              </span>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <strong>刪除行數：</strong>
              <span style={{ color: '#dc3545' }}>
                {diffContent ? (diffContent.match(/^-/gm) || []).length : 0}
              </span>
            </div>
            <div>
              <strong>變更類型：</strong>
              <span style={{ color: '#6f42c1' }}>
                {diffContent ? 
                  (diffContent.includes('new file') ? '新增檔案' : 
                   diffContent.includes('deleted file') ? '刪除檔案' : '修改檔案') : 
                  '未分析'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Diff 輸入區域 */}
      <div style={{ marginBottom: '30px' }}>
        <h2>📝 程式碼變更 (Diff)</h2>
        <textarea
          value={diffContent}
          onChange={(e) => setDiffContent(e.target.value)}
          placeholder="請貼上您的 diff 內容..."
          style={{
            width: '100%',
            height: '300px',
            padding: '15px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontSize: '14px',
            resize: 'vertical'
          }}
        />
        <button
          onClick={handleAnalyzePR}
          disabled={isAnalyzing}
          style={{
            marginTop: '15px',
            padding: '15px 30px',
            backgroundColor: isAnalyzing ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: isAnalyzing ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          {isAnalyzing ? '�� AI 分析中...' : '🔍 開始分析 PR'}
        </button>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      {/* PR 評論 GUI 預覽 */}
      {showCommentGUI && (
        <div style={{ marginBottom: '30px' }}>
          <h2>💬 PR 評論 GUI 預覽</h2>
          <div style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px'
          }}>
            <p style={{ marginBottom: '15px', color: '#6c757d' }}>
              這是模擬在 GitHub/GitLab PR 頁面中會出現的 AI 評論 GUI：
            </p>
            <PRCommentGUI 
              diffContent={diffContent}
              prTitle={prTitle}
              prDescription={prDescription}
              autoAnalyze={true}
            />
          </div>
        </div>
      )}

      {/* 分析結果 */}
      {analysisResult && (
        <div style={{ marginBottom: '30px' }}>
          <h2>🎯 PR 分析結果</h2>
          
          {/* 視覺化摘要卡片 */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
            marginBottom: '30px'
          }}>
            <div style={{
              padding: '20px',
              backgroundColor: '#d4edda',
              borderRadius: '8px',
              border: '1px solid #c3e6cb'
            }}>
              <h3 style={{ color: '#155724', marginBottom: '10px' }}>✅ 變更摘要</h3>
              <ReactMarkdown>{analysisResult.summary}</ReactMarkdown>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#fff3cd',
              borderRadius: '8px',
              border: '1px solid #ffeaa7'
            }}>
              <h3 style={{ color: '#856404', marginBottom: '10px' }}>⚠️ 風險評估</h3>
              <div style={{ fontSize: '14px' }}>
                {analysisResult.analysis.includes('風險') ? 
                  analysisResult.analysis.split('風險')[1]?.split('\n')[0] || '無明顯風險' : 
                  'AI 分析中未發現明顯風險'
                }
              </div>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#d1ecf1',
              borderRadius: '8px',
              border: '1px solid #bee5eb'
            }}>
              <h3 style={{ color: '#0c5460', marginBottom: '10px' }}>💡 建議改進</h3>
              <div style={{ fontSize: '14px' }}>
                {analysisResult.analysis.includes('建議') ? 
                  analysisResult.analysis.split('建議')[1]?.split('\n')[0] || '無特殊建議' : 
                  'AI 分析中無特殊建議'
                }
              </div>
            </div>
          </div>

          {/* 詳細分析 */}
          <div style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            maxHeight: '500px',
            overflowY: 'auto'
          }}>
            <h3 style={{ marginBottom: '15px' }}>📊 詳細分析報告</h3>
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={tomorrow}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {analysisResult.analysis}
            </ReactMarkdown>
          </div>

          {/* 操作按鈕 */}
          <div style={{
            display: 'flex',
            gap: '15px',
            marginTop: '20px',
            justifyContent: 'center'
          }}>
            <button style={{
              padding: '12px 24px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}>
              ✅ 接受 PR
            </button>
            <button style={{
              padding: '12px 24px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}>
              ❌ 拒絕 PR
            </button>
            <button style={{
              padding: '12px 24px',
              backgroundColor: '#ffc107',
              color: '#212529',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}>
              💬 請求修改
            </button>
            <button style={{
              padding: '12px 24px',
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}>
              📋 匯出報告
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PRVisualizer; 