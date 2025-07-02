import { GoogleGenerativeAI } from '@google/generative-ai';

// 初始化 Gemini API
const genAI = new GoogleGenerativeAI('AIzaSyBbqm1YexJ3jQue1DQqZKvI7U4zkvYb6ok');

// 分析 diff 的函數
export const analyzeDiff = async (diffContent) => {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash-lite-preview-06-17" });

    const prompt = `
    請分析以下程式碼變更 (diff)，並提供詳細的分析報告：

    ${diffContent}

    請從以下角度分析：
    1. 變更類型（新增、修改、刪除）
    2. 影響範圍
    3. 潛在風險
    4. 程式碼品質
    5. 建議改進
    6. 測試建議

    請用繁體中文回答，並提供結構化的分析結果。
    `;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error('Gemini API 錯誤:', error);
    throw new Error('無法分析 diff');
  }
};

// 生成 GUI 的函數
export const generateGUI = async (analysisResult, diffContent) => {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash-lite-preview-06-17" });

    const prompt = `
    基於以下分析結果和 diff 內容，請生成一個 React 組件的 JSX 代碼，用於展示分析結果：

    分析結果：
    ${analysisResult}

    Diff 內容：
    ${diffContent}

    請生成一個美觀的 React 組件，包含：
    1. 分析摘要卡片
    2. 詳細分析內容
    3. 風險評估視覺化
    4. 建議改進列表
    5. 互動式元素

    請只返回 JSX 代碼，不要包含其他說明文字。
    `;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error('Gemini GUI 生成錯誤:', error);
    throw new Error('無法生成 GUI');
  }
};

// 解析 Gemini 生成的 JSX
export const parseGeneratedJSX = (jsxString) => {
  try {
    // 移除可能的 markdown 代碼塊標記
    let cleanJSX = jsxString.replace(/```jsx?\n?/g, '').replace(/```\n?/g, '');
    
    // 確保 JSX 是有效的
    if (!cleanJSX.includes('return') && !cleanJSX.includes('export')) {
      cleanJSX = `return (${cleanJSX})`;
    }
    
    return cleanJSX;
  } catch (error) {
    console.error('JSX 解析錯誤:', error);
    return null;
  }
};

// 生成 PR 摘要
export const generatePRSummary = async (prTitle, prDescription, analysisResult) => {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash-lite-preview-06-17" });

    const prompt = `
    基於以下 PR 資訊和分析結果，請生成一個簡潔的 PR 摘要：

    PR 標題：${prTitle}
    PR 描述：${prDescription}
    
    AI 分析結果：
    ${analysisResult}

    請生成一個 2-3 句話的摘要，重點說明：
    1. 這個 PR 的主要目的
    2. 變更的影響範圍
    3. 是否建議合併

    請用繁體中文回答，保持簡潔明瞭。
    `;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error('PR 摘要生成錯誤:', error);
    return '無法生成 PR 摘要';
  }
}; 