import React, { useEffect, useState } from 'react';
import './App.css';
import { initializeRemoteConfig, getFeatureToggle, db } from './firebase.js';
import {
  collection,
  query,
  orderBy,
  onSnapshot,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  serverTimestamp // 新增 serverTimestamp
} from 'firebase/firestore';

function App() {
  const [isNewFeatureEnabled, setIsNewFeatureEnabled] = useState(false);
  const [todos, setTodos] = useState([]);
  const [newTodoText, setNewTodoText] = useState(''); // 新增輸入框的狀態

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

  // 異步函數：新增待辦事項
  const addTodo = async () => {
    if (newTodoText.trim() === '') return; // 如果輸入框為空，則不做任何操作

    try {
      // 使用 addDoc 將新的待辦事項添加到 'todos' 集合
      await addDoc(collection(db, 'todos'), {
        text: newTodoText,
        completed: false,
        createdAt: serverTimestamp() // 使用 Firestore 服務器時間戳
      });
      setNewTodoText(''); // 清空輸入框
    } catch (e) {
      console.error("Error adding document: ", e);
    }
  };

  // 異步函數：切換待辦事項完成狀態 (此階段仍為佔位符)
  const toggleTodoComplete = async (id, completed) => {
    console.log("Toggle ToDo function not yet implemented.");
  };

  // 異步函數：刪除待辦事項 (此階段仍為佔位符)
  const deleteTodo = async (id) => {
    console.log("Delete ToDo function not yet implemented.");
  };

  return (
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
                        <button style={{ padding: '8px 12px', borderRadius: '8px', border: 'none', backgroundColor: '#888', color: 'white', cursor: 'not-allowed' }}>
                          功能未開
                        </button>
                        <button style={{ padding: '8px 12px', borderRadius: '8px', border: 'none', backgroundColor: '#888', color: 'white', cursor: 'not-allowed' }}>
                          功能未開
                        </button>
                      </div>
                    </li>
                ))}
              </ul>
          )}
        </main>
      </div>
  );
}

export default App;