# 🚀 PR 評論 GUI 整合指南

## 概述

這個功能讓您能夠在 GitHub/GitLab PR 頁面中自動顯示 AI 驅動的程式碼分析 GUI，類似 Google Assistant 的提示風格。

## 🎯 功能特色

- **自動觸發**：當訪問 PR 頁面時自動出現
- **AI 分析**：使用 Gemini AI 分析程式碼變更
- **視覺化 GUI**：美觀的卡片式介面展示分析結果
- **即時統計**：顯示檔案變更數、新增/刪除行數等
- **互動操作**：一鍵接受、拒絕、請求修改

## 📦 安裝方式

### 方式一：瀏覽器擴展（推薦）

1. **安裝 Tampermonkey**
   - Chrome: [Tampermonkey](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
   - Firefox: [Tampermonkey](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)

2. **創建新腳本**
   - 點擊 Tampermonkey 圖標
   - 選擇「創建新腳本」

3. **貼上腳本內容**
   ```javascript
   // ==UserScript==
   // @name         AI PR Assistant
   // @namespace    http://tampermonkey.net/
   // @version      1.0
   // @description  AI 驅動的 PR 分析助手
   // @author       Your Name
   // @match        https://github.com/*/pull/*
   // @match        https://gitlab.com/*/merge_requests/*
   // @grant        none
   // ==/UserScript==

   (function() {
       'use strict';
       
       // 等待頁面加載
       function waitForElement(selector, callback) {
           const element = document.querySelector(selector);
           if (element) {
               callback(element);
           } else {
               setTimeout(() => waitForElement(selector, callback), 500);
           }
       }
       
       // 初始化 AI 助手
       function initAIAssistant() {
           const integration = new PRIntegration();
           integration.init();
       }
       
       // 當頁面加載完成時初始化
       if (document.readyState === 'loading') {
           document.addEventListener('DOMContentLoaded', initAIAssistant);
       } else {
           initAIAssistant();
       }
   })();
   ```

4. **保存並啟用**
   - 按 Ctrl+S 保存腳本
   - 確保腳本已啟用

### 方式二：開發者工具

1. **訪問 PR 頁面**
   - 打開 GitHub 或 GitLab 的 PR 頁面

2. **打開開發者工具**
   - 按 F12 或右鍵選擇「檢查」

3. **執行整合代碼**
   ```javascript
   // 複製並執行 src/utils/githubIntegration.js 中的代碼
   const integration = new PRIntegration();
   integration.init();
   ```

## 🔧 配置設定

### 環境變數

**注意**：Gemini API 金鑰已直接配置在程式碼中，無需額外設定環境變數。

### 自訂樣式

您可以修改 `PRCommentGUI.js` 中的樣式來符合您的需求：

```javascript
// 修改顏色主題
const theme = {
  primary: '#0969da',    // 主要顏色
  success: '#28a745',    // 成功顏色
  danger: '#d73a49',     // 危險顏色
  warning: '#ffc107'     // 警告顏色
};
```

## 📱 使用流程

1. **提交 PR**
   - 開發人員 push 新版本並創建 PR

2. **自動觸發**
   - 訪問 PR 頁面時自動顯示 AI 評論 GUI

3. **AI 分析**
   - 系統自動分析 diff 內容
   - 生成結構化分析報告

4. **視覺化展示**
   - 顯示分析摘要卡片
   - 提供詳細分析報告
   - 展示建議操作按鈕

5. **互動操作**
   - 點擊「建議合併」接受 PR
   - 點擊「需要修改」拒絕 PR
   - 點擊「添加評論」提供反饋

## 🎨 GUI 組件說明

### 主要元素

- **🤖 AI 程式碼分析助手**：標題和展開/收起按鈕
- **📊 快速統計**：檔案變更數、新增/刪除行數
- **📋 AI 分析摘要**：簡潔的分析結果
- **📊 詳細分析報告**：可展開的完整報告
- **🎯 操作按鈕**：接受、拒絕、評論、匯出

### 互動功能

- **展開/收起**：點擊標題旁的按鈕
- **詳細報告**：點擊「查看詳細分析報告」
- **操作按鈕**：一鍵執行相應操作

## 🔍 故障排除

### 常見問題

1. **GUI 沒有出現**
   - 檢查是否在正確的 PR 頁面
   - 確認腳本已啟用
   - 檢查瀏覽器控制台是否有錯誤

2. **AI 分析失敗**
   - 確認 API 金鑰已設定
   - 檢查網路連接
   - 查看錯誤訊息

3. **樣式顯示異常**
   - 清除瀏覽器快取
   - 重新載入頁面
   - 檢查 CSS 衝突

### 除錯技巧

```javascript
// 在瀏覽器控制台中檢查
console.log('PR Integration Status:', {
  isPRPage: integration.isPRPage(),
  prInfo: await integration.getPRInfo(),
  container: document.getElementById('ai-pr-comment-gui')
});
```

## 🚀 進階功能

### 自訂分析邏輯

修改 `geminiService.js` 中的 prompt 來調整分析邏輯：

```javascript
const prompt = `
請分析以下程式碼變更，並提供：
1. 變更類型分析
2. 影響範圍評估
3. 潛在風險識別
4. 程式碼品質評估
5. 測試建議
6. 合併建議

${diffContent}
`;
```

### 擴展支援平台

在 `githubIntegration.js` 中添加新平台支援：

```javascript
// 添加新平台檢測
isNewPlatform() {
  return window.location.hostname.includes('your-platform.com');
}

// 添加新平台資訊獲取
async getNewPlatformPRInfo() {
  // 實作新平台的 PR 資訊獲取邏輯
}
```

## 📞 支援

如果您遇到問題或需要協助，請：

1. 檢查本指南的故障排除部分
2. 查看瀏覽器控制台的錯誤訊息
3. 確認所有配置設定正確
4. 聯繫開發團隊尋求協助

---

**注意**：Gemini API 金鑰已直接配置在程式碼中，無需額外設定環境變數。 