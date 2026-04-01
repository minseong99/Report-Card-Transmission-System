import React from 'react';

/**
 * 画面下部に数秒間だけ表示されるトースト通知コンポーネント
 */
export const Toast = ({ message }) => {
    if (!message) return null;
    return (
        <div style={{ position: 'fixed', bottom: '30px', left: '50%', transform: 'translateX(-50%)', backgroundColor: '#334155', color: 'white', padding: '12px 24px', borderRadius: '30px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', zIndex: 1001, fontWeight: 'bold', animation: 'fadeInOut 3s forwards' }}>
            {message}
        </div>
    );
};

/**
 * 重要な操作の前に確認を促すモーダルコンポーネント
 */
export const ConfirmModal = ({ isOpen, title, children, onConfirm, onCancel, confirmText = "はい" }) => {
    if (!isOpen) return null;
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
            <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '12px', width: '400px', textAlign: 'center', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
                <h3 style={{ marginTop: 0, color: '#333' }}>{title}</h3>
                <div style={{ color: '#666', marginBottom: '25px' }}>{children}</div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '15px' }}>
                    <button onClick={onCancel} style={{ padding: '10px 20px', border: '1px solid #cbd5e1', backgroundColor: 'white', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', color: '#64748b' }}>キャンセル</button>
                    <button onClick={onConfirm} style={{ padding: '10px 20px', border: 'none', backgroundColor: '#3b82f6', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', color: 'white' }}>{confirmText}</button>
                </div>
            </div>
        </div>
    );
};

/**
 * テーブル用のページネーションコンポーネント
 */
export const Pagination = ({ currentPage, totalPages, onPageChange }) => {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e2e8f0', gap: '15px' }}>
            <button 
                onClick={() => onPageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                style={{ padding: '8px 16px', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: currentPage === 1 ? '#f8fafc' : 'white', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', color: '#475569', fontWeight: 'bold' }}
            >
                前へ
            </button>
            <span style={{ color: '#64748b', fontWeight: 'bold', fontSize: '14px' }}>
                {currentPage} / {totalPages} ページ
            </span>
            <button 
                onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                style={{ padding: '8px 16px', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: currentPage === totalPages ? '#f8fafc' : 'white', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer', color: '#475569', fontWeight: 'bold' }}
            >
                次へ
            </button>
        </div>
    );
};