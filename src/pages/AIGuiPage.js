import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { analyzeDiff, generateGUI } from '../services/geminiService';
import DOMPurify from 'dompurify';

const AIGuiPage = () => {
  const [searchParams] = useSearchParams();
  const [analysis, setAnalysis] = useState('');
  const [gui, setGui] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 取得 URL 參數
  const title = searchParams.get('title') || '';
  const desc = searchParams.get('desc') || '';
  const diff = searchParams.get('diff') || '';

  useEffect(() => {
    const runAI = async () => {
      if (!diff) return;
      setLoading(true);
      setError('');
      try {
        const analysisResult = await analyzeDiff(diff);
        setAnalysis(analysisResult);
        const guiResult = await generateGUI(analysisResult, diff);
        setGui(guiResult);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    runAI();
  }, [diff]);

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f6f8fa',
      padding: '32px',
      fontFamily: 'Inter, sans-serif',
      boxSizing: 'border-box'
    }}>
      <div style={{ maxWidth: 900, margin: '0 auto', background: 'white', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.08)', padding: 32 }}>
        <h1 style={{ color: '#0969da', marginBottom: 8 }}>🤖 AI PR GUI</h1>
        <div style={{ color: '#555', marginBottom: 24 }}>
          <strong>PR 標題：</strong>{title}<br/>
          <strong>PR 描述：</strong>{desc}
        </div>
        {loading && <div style={{ color: '#888', margin: '24px 0' }}>AI 分析中，請稍候...</div>}
        {error && <div style={{ color: 'red', margin: '24px 0' }}>❌ {error}</div>}
        {gui && (
          <div style={{ marginTop: 24 }}>
            <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(gui) }} />
          </div>
        )}
        {!loading && !gui && !error && (
          <div style={{ color: '#aaa', marginTop: 32 }}>請透過 URL 傳入 diff 參數，例如：<br/><code>?title=...&desc=...&diff=...</code></div>
        )}
      </div>
    </div>
  );
};

export default AIGuiPage; 