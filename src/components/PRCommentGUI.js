import React, { useState, useEffect } from 'react';
import { analyzeDiff, generatePRSummary } from '../services/geminiService';
import ReactMarkdown from 'react-markdown';

const PRCommentGUI = ({ diffContent, prTitle, prDescription, autoAnalyze = true }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (autoAnalyze && diffContent && prTitle) {
      handleAutoAnalyze();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diffContent, prTitle, autoAnalyze]);

  const handleAutoAnalyze = async () => {
    setIsAnalyzing(true);
    setError('');

    try {
      const result = await analyzeDiff(diffContent);
      const summary = await generatePRSummary(prTitle, prDescription || '', result);
      
      setAnalysisResult({
        analysis: result,
        summary: summary
      });
      setIsExpanded(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleManualAnalyze = () => {
    if (!diffContent || !prTitle) {
      setError('缺少必要的 PR 資訊');
      return;
    }
    handleAutoAnalyze();
  };

  // 計算快速統計
  const getQuickStats = () => {
    if (!diffContent) return null;
    
    const fileChanges = diffContent.split('diff --git').length - 1;
    const additions = (diffContent.match(/^\+/gm) || []).length;
    const deletions = (diffContent.match(/^-/gm) || []).length;
    const changeType = diffContent.includes('new file') ? '新增' : 
                      diffContent.includes('deleted file') ? '刪除' : '修改';

    return { fileChanges, additions, deletions, changeType };
  };

  const quickStats = getQuickStats();

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
      fontSize: '14px',
      lineHeight: '1.5',
      color: '#24292f'
    }}>
      {/* 主要提示卡片 */}
      <div style={{
        backgroundColor: '#f6f8fa',
        border: '1px solid #d0d7de',
        borderRadius: '6px',
        padding: '16px',
        marginBottom: '16px',
        position: 'relative'
      }}>
        {/* 標題和展開按鈕 */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: '#0969da',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              🤖
            </div>
            <span style={{ fontWeight: '600', color: '#24292f' }}>
              AI 程式碼分析助手
            </span>
          </div>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'none',
              border: 'none',
              color: '#0969da',
              cursor: 'pointer',
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {isExpanded ? '收起' : '展開'}
            <span style={{ fontSize: '10px' }}>
              {isExpanded ? '▲' : '▼'}
            </span>
          </button>
        </div>

        {/* 快速統計 */}
        {quickStats && (
          <div style={{
            display: 'flex',
            gap: '16px',
            marginBottom: '12px',
            padding: '8px 12px',
            backgroundColor: 'white',
            borderRadius: '4px',
            border: '1px solid #d0d7de'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#656d76' }}>📁</span>
              <span style={{ fontSize: '12px' }}>
                <strong>{quickStats.fileChanges}</strong> 檔案
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#28a745' }}>+</span>
              <span style={{ fontSize: '12px', color: '#28a745' }}>
                <strong>{quickStats.additions}</strong> 新增
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#d73a49' }}>-</span>
              <span style={{ fontSize: '12px', color: '#d73a49' }}>
                <strong>{quickStats.deletions}</strong> 刪除
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#656d76' }}>🔄</span>
              <span style={{ fontSize: '12px' }}>
                <strong>{quickStats.changeType}</strong>
              </span>
            </div>
          </div>
        )}

        {/* 分析狀態 */}
        {isAnalyzing && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            backgroundColor: '#fff3cd',
            border: '1px solid #ffeaa7',
            borderRadius: '4px',
            color: '#856404'
          }}>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid #856404',
              borderTop: '2px solid transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
            <span style={{ fontSize: '13px' }}>AI 正在分析程式碼變更...</span>
          </div>
        )}

        {/* 錯誤訊息 */}
        {error && (
          <div style={{
            padding: '8px 12px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '4px',
            color: '#dc2626',
            fontSize: '13px',
            marginBottom: '12px'
          }}>
            ❌ {error}
          </div>
        )}

        {/* 展開的詳細內容 */}
        {isExpanded && analysisResult && (
          <div style={{ marginTop: '16px' }}>
            {/* 摘要卡片 */}
            <div style={{
              backgroundColor: 'white',
              border: '1px solid #d0d7de',
              borderRadius: '6px',
              padding: '16px',
              marginBottom: '12px'
            }}>
              <h4 style={{
                margin: '0 0 8px 0',
                fontSize: '14px',
                fontWeight: '600',
                color: '#24292f'
              }}>
                📋 AI 分析摘要
              </h4>
              <div style={{ fontSize: '13px', color: '#656d76' }}>
                <ReactMarkdown>{analysisResult.summary}</ReactMarkdown>
              </div>
            </div>

            {/* 詳細分析 */}
            <details style={{ marginBottom: '12px' }}>
              <summary style={{
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '600',
                color: '#0969da',
                padding: '8px 0'
              }}>
                📊 查看詳細分析報告
              </summary>
              <div style={{
                backgroundColor: 'white',
                border: '1px solid #d0d7de',
                borderRadius: '6px',
                padding: '16px',
                marginTop: '8px',
                maxHeight: '300px',
                overflowY: 'auto',
                fontSize: '13px',
                lineHeight: '1.6'
              }}>
                <ReactMarkdown>{analysisResult.analysis}</ReactMarkdown>
              </div>
            </details>

            {/* 操作按鈕 */}
            <div style={{
              display: 'flex',
              gap: '8px',
              flexWrap: 'wrap'
            }}>
              <button style={{
                padding: '6px 12px',
                backgroundColor: '#28a745',
                color: 'white',
                border: '1px solid #28a745',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '500'
              }}>
                ✅ 建議合併
              </button>
              <button style={{
                padding: '6px 12px',
                backgroundColor: '#fff',
                color: '#d73a49',
                border: '1px solid #d73a49',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '500'
              }}>
                ❌ 需要修改
              </button>
              <button style={{
                padding: '6px 12px',
                backgroundColor: '#fff',
                color: '#0969da',
                border: '1px solid #0969da',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '500'
              }}>
                💬 添加評論
              </button>
              <button style={{
                padding: '6px 12px',
                backgroundColor: '#fff',
                color: '#656d76',
                border: '1px solid #d0d7de',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '500'
              }}>
                📋 匯出報告
              </button>
            </div>
          </div>
        )}

        {/* 手動分析按鈕 */}
        {!isAnalyzing && !analysisResult && (
          <button
            onClick={handleManualAnalyze}
            style={{
              padding: '8px 16px',
              backgroundColor: '#0969da',
              color: 'white',
              border: '1px solid #0969da',
              borderRadius: '4px',
              fontSize: '13px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            🔍 開始 AI 分析
          </button>
        )}
      </div>

      {/* CSS 動畫 */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default PRCommentGUI; 