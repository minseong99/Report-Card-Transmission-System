import React from 'react';

/**
 * アプリケーションの共通ヘッダーコンポーネント
 * ログアウト機能などのレイアウトUIを担当します。
 */
export default function Header({ onLogout }) {
    return (
        <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            padding: '15px 30px', 
            backgroundColor: 'white', 
            borderBottom: '1px solid #e2e8f0' 
        }}>
            <h1 style={{ margin: 0, fontSize: '22px', color: '#1e293b' }}>
                成績表送信システム
            </h1>
            
            <button
                onClick={onLogout}
                style={{ 
                    padding: '8px 16px', 
                    backgroundColor: '#7f7d8e', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '5px', 
                    cursor: 'pointer', 
                    fontWeight: 'bold', 
                    transition: '0.2s' 
                }}
            >
                ログアウト
            </button>
        </div>
    );
}