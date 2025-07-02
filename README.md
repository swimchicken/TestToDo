# 🤖 AI 助手專案

這是一個整合了 Firebase 和 Google Gemini AI 的 React 應用程式，提供 Todo 管理功能和智能的程式碼變更分析。

## ✨ 功能特色

### 📝 Todo 管理
- 新增、編輯、刪除待辦事項
- 即時同步到 Firebase Firestore
- 完成狀態切換
- Firebase Remote Config 功能開關

### 🔍 Gemini Diff 分析器
- **智能程式碼分析**：使用 Google Gemini AI 分析程式碼變更
- **動態 GUI 生成**：讓 Gemini 生成美觀的網頁介面來展示分析結果
- **結構化分析報告**：包含變更類型、影響範圍、風險評估等
- **互動式操作**：提供接受、拒絕、修改建議等操作

### 📋 PR 視覺化分析器
- **PR 資訊管理**：輸入 PR 標題、描述和 diff 內容
- **即時統計分析**：自動計算檔案變更數、新增/刪除行數等
- **視覺化摘要卡片**：清晰展示變更摘要、風險評估、建議改進
- **智能分析報告**：AI 驅動的詳細分析，幫助開發者快速理解變更
- **審查操作**：一鍵接受、拒絕、請求修改或匯出報告

### 💬 PR 評論 GUI
- **自動觸發**：當開發人員 push 新版本並提交 PR 時自動出現
- **類似 Google Assistant**：在 PR 頁面下方顯示智能提示 GUI
- **AI 分析流程**：先 AI 分析 diff → AI 產出 GUI 功能
- **GitHub/GitLab 整合**：支援主流程式碼託管平台的 PR 頁面
- **瀏覽器擴展**：可作為瀏覽器擴展在實際 PR 頁面中使用

## 🚀 快速開始

### 1. 安裝依賴
```bash
npm install
```

### 2. 設定環境變數
建立 `.env` 檔案並設定以下變數：
```env
# Firebase 配置
REACT_APP_FIREBASE_API_KEY=your-firebase-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
REACT_APP_FIREBASE_APP_ID=your-app-id
REACT_APP_FIREBASE_MEASUREMENT_ID=your-measurement-id
```

**注意**：Gemini API 金鑰已直接配置在程式碼中，無需額外設定環境變數。

### 3. 啟動開發伺服器
```bash
npm start
```

## 🎯 使用方式

### Todo 功能
1. 點擊「📝 Todo 列表」標籤
2. 在輸入框中輸入待辦事項
3. 點擊「新增」按鈕
4. 使用「標記完成」或「刪除」按鈕管理項目

### Diff 分析器
1. 點擊「🔍 Diff 分析器」標籤
2. 在文字區域貼上您的 diff 內容
3. 點擊「🔍 分析 Diff」按鈕
4. 等待 Gemini AI 分析完成
5. 點擊「🎨 生成 GUI」來創建動態展示介面

### PR 視覺化分析器
1. 點擊「📋 PR 視覺化」標籤
2. 填寫 PR 標題和描述
3. 貼上 diff 內容
4. 點擊「🔍 開始分析 PR」按鈕
5. 查看視覺化分析結果和建議操作

### PR 評論 GUI 整合
1. **瀏覽器擴展方式**：
   - 安裝 Tampermonkey 擴展
   - 創建新腳本並貼上 `src/utils/githubIntegration.js` 中的腳本
   - 訪問 GitHub/GitLab PR 頁面時自動觸發

2. **開發者工具方式**：
   - 在 PR 頁面打開開發者工具
   - 執行 `src/utils/githubIntegration.js` 中的整合代碼
   - AI 評論 GUI 將自動出現在 PR 頁面中

## 🛠️ 技術架構

### 前端
- **React 19** - 現代化 UI 框架
- **Firebase** - 後端服務和即時資料庫
- **Google Gemini AI** - 智能程式碼分析
- **React Markdown** - Markdown 渲染
- **Syntax Highlighter** - 程式碼語法高亮

### 後端服務
- **Firebase Firestore** - 即時資料庫
- **Firebase Remote Config** - 功能開關管理
- **Google Gemini API** - AI 分析服務

## 📁 專案結構

```
src/
├── components/
│   ├── DiffAnalyzer.js      # Diff 分析器主組件
│   ├── PRVisualizer.js      # PR 視覺化分析器
│   ├── PRCommentGUI.js      # PR 評論 GUI 組件
│   └── GUIRenderer.js       # 動態 GUI 渲染器
├── services/
│   └── geminiService.js     # Gemini API 服務
├── utils/
│   └── githubIntegration.js # GitHub/GitLab 整合工具
├── App.js                   # 主應用程式
├── firebase.js             # Firebase 配置
└── index.js                # 應用程式入口
```

## 🔧 開發指南

### 新增功能
1. 在 `src/components/` 建立新組件
2. 在 `src/services/` 建立相關服務
3. 更新 `App.js` 整合新功能

### 自訂 Gemini 分析
修改 `src/services/geminiService.js` 中的 prompt 來調整分析邏輯。

### 自訂 GUI 生成
調整 `generateGUI` 函數中的 prompt 來改變生成的介面風格。

## 🤝 貢獻

歡迎提交 Pull Request 或開立 Issue！

## 📄 授權

MIT License

## 🔗 相關連結

- [Google Gemini API](https://ai.google.dev/)
- [Firebase 文件](https://firebase.google.com/docs)
- [React 文件](https://react.dev/)
