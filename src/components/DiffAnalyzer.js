import React, { useState } from 'react';
import { analyzeDiff, generateGUI, parseGeneratedJSX } from '../services/geminiService';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const DiffAnalyzer = () => {
  const [diffContent, setDiffContent] = useState('');
  const [analysisResult, setAnalysisResult] = useState('');
  const [generatedGUI, setGeneratedGUI] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingGUI, setIsGeneratingGUI] = useState(false);
  const [error, setError] = useState('');

  // 示例 diff 內容
  const sampleDiff = `diff --git a/src/App.js b/src/App.js
index 1234567..abcdefg 100644
--- a/src/App.js
+++ b/src/App.js
@@ -10,6 +10,7 @@ function App() {
   const [todos, setTodos] = useState([]);
   const [newTodoText, setNewTodoText] = useState('');
+  const [isLoading, setIsLoading] = useState(false);
 
   useEffect(() => {
     initializeRemoteConfig().then(() => {
@@ -45,6 +46,7 @@ function App() {
   const addTodo = async () => {
     if (newTodoText.trim() === '') return;
 
+    setIsLoading(true);
     try {
       await addDoc(collection(db, 'todos'), {
         text: newTodoText,
@@ -52,6 +54,7 @@ function App() {
         createdAt: serverTimestamp()
       });
       setNewTodoText('');
+      setIsLoading(false);
     } catch (e) {
       console.error("Error adding document: ", e);
+      setIsLoading(false);
     }
   };`;

  const handleAnalyzeDiff = async () => {
    if (!diffContent.trim()) {
      setError('請輸入 diff 內容');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const result = await analyzeDiff(diffContent);
      setAnalysisResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateGUI = async () => {
    if (!analysisResult) {
      setError('請先分析 diff');
      return;
    }

    setIsGeneratingGUI(true);
    setError('');

    try {
      const guiJSX = await generateGUI(analysisResult, diffContent);
      const parsedJSX = parseGeneratedJSX(guiJSX);
      setGeneratedGUI(parsedJSX);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGeneratingGUI(false);
    }
  };

  const loadSampleDiff = () => {
    setDiffContent(sampleDiff);
  };

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'Inter, sans-serif'
    }}>
      <h1 style={{ 
        textAlign: 'center', 
        color: '#333',
        marginBottom: '30px'
      }}>
        🤖 Gemini Diff 分析器
      </h1>

      {/* Diff 輸入區域 */}
      <div style={{ marginBottom: '30px' }}>
        <h2>📝 輸入 Diff 內容</h2>
        <div style={{ marginBottom: '10px' }}>
          <button 
            onClick={loadSampleDiff}
            style={{
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            載入示例
          </button>
        </div>
        <textarea
          value={diffContent}
          onChange={(e) => setDiffContent(e.target.value)}
          placeholder="請貼上您的 diff 內容..."
          style={{
            width: '100%',
            height: '200px',
            padding: '15px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontSize: '14px',
            resize: 'vertical'
          }}
        />
        <button
          onClick={handleAnalyzeDiff}
          disabled={isAnalyzing}
          style={{
            marginTop: '10px',
            padding: '12px 24px',
            backgroundColor: isAnalyzing ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isAnalyzing ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {isAnalyzing ? '分析中...' : '🔍 分析 Diff'}
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

      {/* 分析結果 */}
      {analysisResult && (
        <div style={{ marginBottom: '30px' }}>
          <h2>📊 Gemini 分析結果</h2>
          <div style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
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
              {analysisResult}
            </ReactMarkdown>
          </div>
          
          <button
            onClick={handleGenerateGUI}
            disabled={isGeneratingGUI}
            style={{
              marginTop: '15px',
              padding: '12px 24px',
              backgroundColor: isGeneratingGUI ? '#ccc' : '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isGeneratingGUI ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            {isGeneratingGUI ? '生成中...' : '🎨 生成 GUI'}
          </button>
        </div>
      )}

      {/* 生成的 GUI */}
      {generatedGUI && (
        <div style={{ marginBottom: '30px' }}>
          <h2>🎨 Gemini 生成的 GUI</h2>
          <div style={{
            padding: '20px',
            backgroundColor: '#fff',
            border: '2px solid #007bff',
            borderRadius: '8px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
          }}>
            <div dangerouslySetInnerHTML={{ __html: generatedGUI }} />
          </div>
        </div>
      )}
    </div>
  );
};

export default DiffAnalyzer; 