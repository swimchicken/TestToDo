// src/App.js
import React, { useEffect, useState } from 'react';
import './App.css';
// 將 .ts 改為 .js 導入
import { initializeRemoteConfig, getFeatureToggle } from './firebase.js';

function App() {
  const [isNewFeatureEnabled, setIsNewFeatureEnabled] = useState(false);

  useEffect(() => {
    initializeRemoteConfig().then(() => {
      const enabled = getFeatureToggle('new_todo_feature_enabled');
      setIsNewFeatureEnabled(enabled);
      console.log(`Feature 'new_todo_feature_enabled' is: ${enabled ? '啟用' : '禁用'}`);
    });
  }, []);

  return (
      <div className="App">
        <header className="App-header">
          <h1>我的 ToDo List ({isNewFeatureEnabled ? "新功能啟用中" : "基本功能"})</h1>
          {isNewFeatureEnabled ? (
              <p>恭喜！你已經成功啟用了一個新功能區塊。</p>
          ) : (
              <p>新功能目前在測試中，尚未對外開放。</p>
          )}
          <p>請打開瀏覽器控制台查看 Firebase Remote Config 的狀態。</p>
        </header>
      </div>
  );
}

export default App;