import React from 'react';
import { useLogin } from '../hooks/useLogin'; // 🌟 分離したカスタムフックをインポート
import './Login.css';

/**
 * ログイン画面のView（見た目）コンポーネント
 * ロジックはすべて `useLogin` フックに委譲し、UIの描画のみに専念します。
 */
export default function Login({ onLoginSuccess }) {
    // カスタムフックから状態とアクション関数を取得
    const {
        loginId, setLoginId,
        password, setPassword,
        errorMessage, isLoading,
        handleLogin
    } = useLogin(onLoginSuccess);

    return (
        <div className="login-container">
            <div className="login-box">
                {/* ヘッダー領域 */}
                <h2 className="login-title">講師ログイン</h2>
                <p className="login-subtitle">成績表送信システムへようこそ</p>

                {/* エラーメッセージ表示領域（エラーがある時だけ描画） */}
                {errorMessage && <div className="error-message">{errorMessage}</div>}

                {/* ログインフォーム */}
                <form onSubmit={handleLogin}>
                    
                    {/* ID入力欄 */}
                    <div className="input-group">
                        <label>ログイン ID</label>
                        <input
                            type="text"
                            placeholder="IDを入力"
                            value={loginId}
                            onChange={(e) => setLoginId(e.target.value)}
                            disabled={isLoading} // 通信中は入力をブロック
                        />
                    </div>

                    {/* パスワード入力欄 */}
                    <div className="input-group">
                        <label>パスワード</label>
                        <input
                            type="password"
                            placeholder="パスワードを入力"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading} // 通信中は入力をブロック
                        />
                    </div>

                    {/* 送信ボタン */}
                    <button type="submit" className="login-button" disabled={isLoading}>
                        {isLoading ? '確認中...' : 'ログイン'} 
                    </button>
                </form>
            </div>
        </div>
    );
}