// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getRemoteConfig, fetchAndActivate, getValue } from 'firebase/remote-config';
import { getAnalytics } from "firebase/analytics";

// FirebaseConfig
const firebaseConfig = {
    apiKey: "AIzaSyD4iXxfM185gexBWPKcLHxqDMyI65uFLNQ",
    authDomain: "my-todo-app-ac3a5.firebaseapp.com",
    projectId: "my-todo-app-ac3a5",
    storageBucket: "my-todo-app-ac3a5.firebasestorage.app",
    messagingSenderId: "199471858974",
    appId: "1:199471858974:web:ad732dc1f96a5f24e3750f",
    measurementId: "G-T9TC8CJ842"
};

// init Firebase
const app = initializeApp(firebaseConfig);

// get fireStore
export const db = getFirestore(app);

// get RemoteConfig
const remoteConfig = getRemoteConfig(app);


// const analytics = getAnalytics(app);

// update time
remoteConfig.settings.minimumFetchIntervalMillis = 0; // 開發時設為 0 毫秒，立即檢查
remoteConfig.defaultConfig = {
    "new_todo_feature_enabled": false // 本地預設值
};

// await to RemoteConfig
export const initializeRemoteConfig = async () => {
    try {
        await fetchAndActivate(remoteConfig);
        console.log('Firebase Remote Config activated successfully.');
    } catch (err) {
        console.error('Failed to activate Remote Config:', err);
    }
};

// get value(bool)
export const getFeatureToggle = (key) => {
    return getValue(remoteConfig, key).asBoolean();
};