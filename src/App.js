// src/App.js (只展示核心修改，保留之前的 Feature Toggle 邏輯)
import React, { useEffect, useState } from 'react';
import './App.css';
import { initializeRemoteConfig, getFeatureToggle, db } from './firebase.js'; // 導入 db
import { collection, query, orderBy, onSnapshot,addDoc,serverTimestamp } from 'firebase/firestore'; // 導入 Firestore 相關方法


function App() {
  const [isNewFeatureEnabled, setIsNewFeatureEnabled] = useState(false);
  const [todos, setTodos] = useState([]); // 新增 todos 狀態來儲存待辦事項
  const [newTodoText,setNewTodoText] = useState(''); // 新增輸入框的狀態


  useEffect(() => {
    // 初始化 Remote Config
    initializeRemoteConfig().then(() => {
      setIsNewFeatureEnabled(getFeatureToggle('new_todo_feature_enabled'));
    });

    // 訂閱 Firestore 'todos' 集合
    // 查詢：從 'todos' 集合中獲取數據，並按 'createdAt' 降序排列
    const q = query(collection(db, 'todos'), orderBy('createdAt', 'desc'));

    // onSnapshot 會建立一個實時監聽器
    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const todosData = [];
      querySnapshot.forEach((doc) => {
        // 對於每個文件，提取其 ID 和數據
        todosData.push({ id: doc.id, ...doc.data() });
      });
      setTodos(todosData); // 更新狀態，觸發組件重新渲染
    });

    // 清理函數：當組件卸載時，取消 Firestore 監聽，避免記憶體洩漏
    return () => unsubscribe();
  }, []); // 空依賴項確保只在組件首次渲染時執行一次

  return (
      <div className="App">
        <header className="App-header">
          <h1>我的 ToDo List ({isNewFeatureEnabled ? "新功能啟用中" : "基本功能"})</h1>
          {isNewFeatureEnabled ? (
              <p>恭喜！你已經成功啟用了一個新功能區塊。</p>
          ) : (
              <p>新功能目前在測試中，尚未對外開放。</p>
          )}

          <h2 style={{ marginTop: '20px' }}>待辦事項：</h2>
          {todos.length === 0 ? (
              <p>目前沒有待辦事項。</p>
          ) : (
              <ul>
                {todos.map((todo) => (
                    <li key={todo.id} style={{ listStyle: 'none', margin: '10px 0' }}>
                      {todo.text} - {todo.completed ? '已完成' : '未完成'}
                    </li>
                ))}
              </ul>
          )}
        </header>
      </div>
  );
}

export default App;