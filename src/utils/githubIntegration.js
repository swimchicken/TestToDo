// GitHub/GitLab PR 整合工具
// 這個檔案展示了如何在實際的 PR 頁面中嵌入 AI 評論 GUI

export class PRIntegration {
  constructor() {
    this.isGitHub = window.location.hostname.includes('github.com');
    this.isGitLab = window.location.hostname.includes('gitlab.com');
    this.apiKey = process.env.REACT_APP_GEMINI_API_KEY;
  }

  // 檢測是否在 PR 頁面
  isPRPage() {
    if (this.isGitHub) {
      return window.location.pathname.includes('/pull/');
    } else if (this.isGitLab) {
      return window.location.pathname.includes('/merge_requests/');
    }
    return false;
  }

  // 獲取 PR 資訊
  async getPRInfo() {
    if (this.isGitHub) {
      return this.getGitHubPRInfo();
    } else if (this.isGitLab) {
      return this.getGitLabPRInfo();
    }
    return null;
  }

  // 獲取 GitHub PR 資訊
  async getGitHubPRInfo() {
    try {
      // 從頁面元素獲取 PR 資訊
      const titleElement = document.querySelector('.gh-header-title .js-issue-title');
      const descriptionElement = document.querySelector('.comment-body');
      const diffElement = document.querySelector('.diff-view');

      if (!titleElement) return null;

      return {
        title: titleElement.textContent.trim(),
        description: descriptionElement ? descriptionElement.textContent.trim() : '',
        diffContent: diffElement ? diffElement.textContent : '',
        platform: 'github'
      };
    } catch (error) {
      console.error('獲取 GitHub PR 資訊失敗:', error);
      return null;
    }
  }

  // 獲取 GitLab PR 資訊
  async getGitLabPRInfo() {
    try {
      const titleElement = document.querySelector('.title');
      const descriptionElement = document.querySelector('.description');
      const diffElement = document.querySelector('.diff-content');

      if (!titleElement) return null;

      return {
        title: titleElement.textContent.trim(),
        description: descriptionElement ? descriptionElement.textContent.trim() : '',
        diffContent: diffElement ? diffElement.textContent : '',
        platform: 'gitlab'
      };
    } catch (error) {
      console.error('獲取 GitLab PR 資訊失敗:', error);
      return null;
    }
  }

  // 在 PR 頁面中插入 AI 評論 GUI
  async insertAIGUI() {
    if (!this.isPRPage()) return;

    const prInfo = await this.getPRInfo();
    if (!prInfo) return;

    // 創建容器
    const container = document.createElement('div');
    container.id = 'ai-pr-comment-gui';
    container.style.cssText = `
      margin: 16px 0;
      padding: 16px;
      background-color: #f6f8fa;
      border: 1px solid #d0d7de;
      border-radius: 6px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    `;

    // 插入到適當位置
    const targetElement = this.findInsertTarget();
    if (targetElement) {
      targetElement.insertBefore(container, targetElement.firstChild);
      
      // 這裡會渲染 React 組件
      this.renderAIGUI(container, prInfo);
    }
  }

  // 找到插入目標元素
  findInsertTarget() {
    if (this.isGitHub) {
      // GitHub: 插入到評論區域
      return document.querySelector('.js-discussion');
    } else if (this.isGitLab) {
      // GitLab: 插入到討論區域
      return document.querySelector('.merge-request-discussions');
    }
    return null;
  }

  // 渲染 AI GUI（這裡需要 React 組件）
  renderAIGUI(container, prInfo) {
    // 注意：在實際實作中，這裡需要 React 的 render 方法
    // 由於這是純 JavaScript 環境，我們先創建一個簡單的 HTML 版本
    
    container.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
        <div style="
          width: 20px;
          height: 20px;
          background-color: #0969da;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 12px;
          font-weight: bold;
        ">🤖</div>
        <span style="font-weight: 600; color: #24292f;">
          AI 程式碼分析助手
        </span>
        <button id="ai-expand-btn" style="
          margin-left: auto;
          background: none;
          border: none;
          color: #0969da;
          cursor: pointer;
          font-size: 12px;
          padding: 4px 8px;
          border-radius: 4px;
        ">展開 ▼</button>
      </div>
      
      <div id="ai-content" style="display: none;">
        <div style="
          padding: 12px;
          background-color: white;
          border: 1px solid #d0d7de;
          border-radius: 4px;
          margin-bottom: 12px;
          font-size: 13px;
        ">
          <strong>PR 標題:</strong> ${prInfo.title}<br>
          <strong>平台:</strong> ${prInfo.platform}<br>
          <strong>狀態:</strong> 正在分析中...
        </div>
        
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button style="
            padding: 6px 12px;
            background-color: #28a745;
            color: white;
            border: 1px solid #28a745;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 500;
          ">✅ 建議合併</button>
          <button style="
            padding: 6px 12px;
            background-color: #fff;
            color: #d73a49;
            border: 1px solid #d73a49;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 500;
          ">❌ 需要修改</button>
          <button style="
            padding: 6px 12px;
            background-color: #fff;
            color: #0969da;
            border: 1px solid #0969da;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 500;
          ">💬 添加評論</button>
        </div>
      </div>
    `;

    // 添加展開/收起功能
    const expandBtn = container.querySelector('#ai-expand-btn');
    const content = container.querySelector('#ai-content');
    
    expandBtn.addEventListener('click', () => {
      const isExpanded = content.style.display !== 'none';
      content.style.display = isExpanded ? 'none' : 'block';
      expandBtn.textContent = isExpanded ? '展開 ▼' : '收起 ▲';
    });
  }

  // 初始化整合
  init() {
    if (this.isPRPage()) {
      // 等待頁面加載完成
      setTimeout(() => {
        this.insertAIGUI();
      }, 2000);
    }
  }
}

// 瀏覽器擴展腳本範例
export const browserExtensionScript = `
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
`;

// 使用範例
export const usageExample = `
// 在您的專案中使用這個整合

import { PRIntegration } from './utils/githubIntegration';

// 初始化整合
const integration = new PRIntegration();

// 檢查是否在 PR 頁面並插入 AI GUI
if (integration.isPRPage()) {
  integration.insertAIGUI();
}

// 或者使用瀏覽器擴展
// 1. 安裝 Tampermonkey
// 2. 創建新腳本
// 3. 貼上 browserExtensionScript 的內容
// 4. 保存並啟用
`; 