// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getRemoteConfig, fetchAndActivate, getValue } from 'firebase/remote-config';
import { getAnalytics } from "firebase/analytics";

// 從 Firebase Console 複製過來的配置
const firebaseConfig = {
    apiKey: "AIzaSyD4iXxfM185gexBWPKcLHxqDMyI65uFLNQ",
    authDomain: "my-todo-app-ac3a5.firebaseapp.com",
    projectId: "my-todo-app-ac3a5",
    storageBucket: "my-todo-app-ac3a5.firebasestorage.app",
    messagingSenderId: "199471858974",
    appId: "1:199471858974:web:ad732dc1f96a5f24e3750f",
    measurementId: "G-T9TC8CJ842"
};

// 初始化 Firebase
const app = initializeApp(firebaseConfig);

// 獲取 Firestore 實例
export const db = getFirestore(app);

// 獲取 Remote Config 實例
const remoteConfig = getRemoteConfig(app);

// 初始化 Analytics (可選，如果你不使用 Analytics 可以移除)
const analytics = getAnalytics(app);

// 設定開發模式下的最小擷取間隔（生產環境下應更長）
remoteConfig.settings.minimumFetchIntervalMillis = 0; // 開發時設為 0 毫秒，立即檢查
remoteConfig.defaultConfig = {
    "new_todo_feature_enabled": false // 本地預設值
};

// 異步函數來初始化和獲取 Remote Config
export const initializeRemoteConfig = async () => {
    try {
        await fetchAndActivate(remoteConfig);
        console.log('Firebase Remote Config activated successfully.');
    } catch (err) {
        console.error('Failed to activate Remote Config:', err);
    }
};

// 獲取 Feature Toggle 值
export const getFeatureToggle = (key) => { // 移除 : string
    return getValue(remoteConfig, key).asBoolean();
};