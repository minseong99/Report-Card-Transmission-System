import { useState } from 'react';
import axios from 'axios'
import './Login.css'

export default function Login ({ onLoginSuccess }) {
    const [loginId, setLoginId] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [isLoading, setIsLoding] = useState(false);

    // ログインボタンのアクション
    const handleLogin = async (e) => {
        e.preventDefault(); // 画面の無駄なリロードを防ぐ
        setErrorMessage('');

        // 入力チェック
        if (!loginId || !password) {
            setErrorMessage('IDとパスワードを入力してください。');
            return;
        }

        setIsLoding(true);

        try {
            //実際のバックエンドAPIにRequestを送る
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type':'application/json',
                },
                body: JSON.stringify({
                    login_id: loginId,
                    password: password
                }),
            });

            if (response.ok){
                const data = await response.json();
                console.log("ログイン成功, 発行されたトークン", data.access_token);
                
                // session 
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('teacher', JSON.stringify(data.teacher))
                onLoginSuccess(data.teacher);
            } else{
                const errorData = await response.json();
                setErrorMessage(errorData.detail || 'IDまたはパスワードが間違っています。');
            }
        } catch (error) {
            console.error('API通信エラー:' ,error);
            setErrorMessage('サーバとの通信に失敗しました。バックエンドを起動しているか確認してください。');
        } finally {
            setIsLoding(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-box">
                <h2 className="login-title">講師ログイン</h2>
                <p className="login-subtitle">成績表送信システムへようこそ</p>

                {errorMessage && <div className="error-message">{errorMessage}</div>}

                <form onSubmit={handleLogin}>
                    <div className="input-group">
                        <label>ログイン ID</label>
                        <input
                            type="text"
                            placeholder="idを入力"
                            value={loginId}
                            onChange={(e) => setLoginId(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="input-group">
                        <label>パスワード</label>
                        <input
                            type="password"
                            placeholder="パスワードを入力"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <button type="submit" className="login-button" disabled={isLoading}>
                        {isLoading ? '確認中...':'ログイン'} 
                    </button>
                </form>
            </div>
        </div>
    );
}