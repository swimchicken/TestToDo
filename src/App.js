import React, { useEffect, useState } from 'react';
import './App.css';
import { initializeRemoteConfig, getFeatureToggle, db } from './firebase.js';
import {
  collection,
  query,
  orderBy,
  onSnapshot,
  addDoc,
  updateDoc, // 導入 updateDoc
  deleteDoc, // 導入 deleteDoc
  doc, // 導入 doc 函數來獲取文件引用
  serverTimestamp
} from 'firebase/firestore';
import DiffAnalyzer from './components/DiffAnalyzer';
import PRVisualizer from './components/PRVisualizer';

function App() {
  const [isNewFeatureEnabled, setIsNewFeatureEnabled] = useState(false);
  const [todos, setTodos] = useState([]);
  const [newTodoText, setNewTodoText] = useState('');
  const [currentView, setCurrentView] = useState('todo'); // 'todo', 'diff', 或 'pr'

  useEffect(() => {
    initializeRemoteConfig().then(() => {
      const enabled = getFeatureToggle('new_todo_feature_enabled');
      setIsNewFeatureEnabled(enabled);
      console.log(`Feature 'new_todo_feature_enabled' is: ${enabled ? '啟用' : '禁用'}`);
    });

    const q = query(collection(db, 'todos'), orderBy('createdAt', 'desc'));

    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const todosData = [];
      querySnapshot.forEach((doc) => {
        todosData.push({ id: doc.id, ...doc.data() });
      });
      setTodos(todosData);
    }, (error) => {
      console.error("Error fetching todos: ", error);
    });

    return () => unsubscribe();
  }, []);

  const addTodo = async () => {
    if (newTodoText.trim() === '') return;

    try {
      await addDoc(collection(db, 'todos'), {
        text: newTodoText,
        completed: false,
        createdAt: serverTimestamp()
      });
      setNewTodoText('');
    } catch (e) {
      console.error("Error adding document: ", e);
    }
  };

  // 異步函數：切換待辦事項的完成狀態
  const toggleTodoComplete = async (id, completed) => {
    // 獲取特定文件的引用
    const todoRef = doc(db, 'todos', id);
    // 更新文件的 'completed' 字段
    await updateDoc(todoRef, {
      completed: !completed // 將當前狀態反轉
    });
  };

  // 異步函數：刪除待辦事項
  const deleteTodo = async (id) => {
    // 獲取特定文件的引用
    const todoRef = doc(db, 'todos', id);
    // 刪除文件
    await deleteDoc(todoRef);
  };

  const TodoView = () => (
    <div className="App" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#282c34',
      color: 'white',
      fontFamily: 'Inter, sans-serif'
    }}>
      <header className="App-header" style={{ textAlign: 'center', padding: '20px', borderRadius: '8px', boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)', backgroundColor: '#333' }}>
        <h1>我的 ToDo List ({isNewFeatureEnabled ? "新功能啟用中" : "基本功能"})</h1>
        {isNewFeatureEnabled ? (
            <p style={{ color: '#61dafb' }}>恭喜！你已經成功啟用了一個新功能區塊。</p>
        ) : (
            <p style={{ color: '#aaa' }}>新功能目前在測試中，尚未對外開放。</p>
        )}
        <p style={{ fontSize: '0.8em', color: '#bbb' }}>請打開瀏覽器控制台查看 Firebase Remote Config 的狀態。</p>
      </header>

      <main style={{ marginTop: '30px', width: '90%', maxWidth: '600px' }}>
        <h2 style={{ marginBottom: '15px' }}>待辦事項：</h2>

        {/* 新增待辦事項區塊 */}
        <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'center' }}>
          <input
              type="text"
              value={newTodoText}
              onChange={(e) => setNewTodoText(e.target.value)}
              placeholder="新增待辦事項..."
              style={{
                padding: '10px 15px',
                marginRight: '10px',
                borderRadius: '8px',
                border: '1px solid #61dafb',
                backgroundColor: '#444',
                color: 'white',
                fontSize: '1em',
                flexGrow: 1
              }}
          />
          <button
              onClick={addTodo}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: '#61dafb',
                color: 'white',
                fontSize: '1em',
                cursor: 'pointer',
                transition: 'background-color 0.3s ease',
              }}
          >
            新增
          </button>
        </div>

        {/* 待辦事項列表顯示 */}
        {todos.length === 0 ? (
            <p style={{ color: '#aaa' }}>目前沒有待辦事項。試著新增一個吧！</p>
        ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {todos.map((todo) => (
                  <li
                      key={todo.id}
                      style={{
                        margin: '15px 0',
                        padding: '15px',
                        borderRadius: '8px',
                        backgroundColor: '#444',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                        transition: 'background-color 0.3s ease',
                        color: todo.completed ? '#aaa' : 'white',
                        textDecoration: todo.completed ? 'line-through' : 'none',
                      }}
                  >
                    <span style={{ flexGrow: 1, textAlign: 'left', fontSize: '1.1em' }}>{todo.text}</span>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                          onClick={() => toggleTodoComplete(todo.id, todo.completed)}
                          style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            border: 'none',
                            backgroundColor: todo.completed ? '#f0ad4e' : '#5cb85c', // 完成/未完成不同顏色
                            color: 'white',
                            cursor: 'pointer',
                            transition: 'background-color 0.3s ease',
                          }}
                      >
                        {todo.completed ? '標記未完成' : '標記完成'}
                      </button>
                      <button
                          onClick={() => deleteTodo(todo.id)}
                          style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            border: 'none',
                            backgroundColor: '#d9534f', // 紅色刪除按鈕
                            color: 'white',
                            cursor: 'pointer',
                            transition: 'background-color 0.3s ease',
                          }}
                      >
                        刪除
                      </button>
                    </div>
                  </li>
              ))}
            </ul>
        )}
      </main>
    </div>
  );

  return (
    <div>
      {/* 導航欄 */}
      <nav style={{
        backgroundColor: '#333',
        padding: '15px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        color: 'white',
        fontFamily: 'Inter, sans-serif'
      }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>🤖 AI 助手專案</h1>
        <div style={{ display: 'flex', gap: '15px' }}>
          <button
            onClick={() => setCurrentView('todo')}
            style={{
              padding: '10px 20px',
              backgroundColor: currentView === 'todo' ? '#61dafb' : '#555',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            📝 Todo 列表
          </button>
          <button
            onClick={() => setCurrentView('diff')}
            style={{
              padding: '10px 20px',
              backgroundColor: currentView === 'diff' ? '#61dafb' : '#555',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            🔍 Diff 分析器
          </button>
          <button
            onClick={() => setCurrentView('pr')}
            style={{
              padding: '10px 20px',
              backgroundColor: currentView === 'pr' ? '#61dafb' : '#555',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            📋 PR 視覺化
          </button>
        </div>
      </nav>

      {/* 主要內容區域 */}
      {currentView === 'todo' ? <TodoView /> : 
       currentView === 'diff' ? <DiffAnalyzer /> : 
       <PRVisualizer />}
    </div>
  );
}

export default App;
