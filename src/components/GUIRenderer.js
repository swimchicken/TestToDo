import React from 'react';
import ReactMarkdown from 'react-markdown';

const GUIRenderer = ({ content, analysisResult, diffContent }) => {
  // 安全的 HTML 渲染函數
  const renderSafeHTML = (htmlString) => {
    // 移除危險的標籤和屬性
    const sanitizedHTML = htmlString
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
      .replace(/on\w+\s*=/gi, '')
      .replace(/javascript:/gi, '');
    
    return { __html: sanitizedHTML };
  };

  // 如果內容是 JSX 格式，嘗試渲染為 React 組件
  const renderJSXContent = () => {
    try {
      // 這裡我們會創建一個動態組件
      // 注意：這只是概念性的，實際實現需要更複雜的邏輯
      return (
        <div style={{
          padding: '20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <h3>🎨 動態生成的 GUI</h3>
          <div dangerouslySetInnerHTML={renderSafeHTML(content)} />
        </div>
      );
    } catch (error) {
      console.error('JSX 渲染錯誤:', error);
      return renderFallbackContent();
    }
  };

  // 後備內容渲染
  const renderFallbackContent = () => {
    return (
      <div style={{
        padding: '20px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        border: '1px solid #007bff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ color: '#007bff', marginBottom: '15px' }}>
          🤖 Gemini 分析結果展示
        </h3>
        
        {/* 分析摘要 */}
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ color: '#28a745' }}>📊 分析摘要</h4>
          <div style={{
            padding: '15px',
            backgroundColor: '#d4edda',
            borderRadius: '6px',
            border: '1px solid #c3e6cb'
          }}>
            <ReactMarkdown>{analysisResult}</ReactMarkdown>
          </div>
        </div>

        {/* Diff 內容 */}
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ color: '#17a2b8' }}>📝 程式碼變更</h4>
          <pre style={{
            padding: '15px',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            border: '1px solid #dee2e6',
            overflow: 'auto',
            fontSize: '12px',
            lineHeight: '1.4'
          }}>
            {diffContent}
          </pre>
        </div>

        {/* 互動式元素 */}
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ color: '#6f42c1' }}>🎯 建議操作</h4>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button style={{
              padding: '8px 16px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}>
              ✅ 接受變更
            </button>
            <button style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}>
              ❌ 拒絕變更
            </button>
            <button style={{
              padding: '8px 16px',
              backgroundColor: '#ffc107',
              color: '#212529',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}>
              💬 請求修改
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ marginTop: '20px' }}>
      {content ? renderJSXContent() : renderFallbackContent()}
    </div>
  );
};

export default GUIRenderer; 