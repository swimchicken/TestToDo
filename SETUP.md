# 🚀 設定指南

## 環境變數設定

請在專案根目錄建立 `.env` 檔案，並加入以下內容：

```env
# Firebase 配置（如果需要）
REACT_APP_FIREBASE_API_KEY=AIzaSyD4iXxfM185gexBWPKcLHxqDMyI65uFLNQ
REACT_APP_FIREBASE_AUTH_DOMAIN=my-todo-app-ac3a5.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=my-todo-app-ac3a5
REACT_APP_FIREBASE_STORAGE_BUCKET=my-todo-app-ac3a5.firebasestorage.app
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=199471858974
REACT_APP_FIREBASE_APP_ID=1:199471858974:web:ad732dc1f96a5f24e3750f
REACT_APP_FIREBASE_MEASUREMENT_ID=G-T9TC8CJ842
```

**注意**：Gemini API 金鑰已直接配置在程式碼中，無需額外設定環境變數。

## 啟動應用程式

```bash
npm start
```

應用程式將在 http://localhost:3000 啟動 