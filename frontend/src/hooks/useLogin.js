import { useState } from 'react';

/**
 * ログイン処理のビジネスロジックを管理するカスタムフック
 * UI（画面の見た目）と通信・状態管理を分離することで、メンテナンス性を高めます。
 */
export function useLogin(onLoginSuccess) {
    // フォームの入力状態
    const [loginId, setLoginId] = useState('');
    const [password, setPassword] = useState('');
    
    // エラーメッセージとローディング状態
    const [errorMessage, setErrorMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false); // typo修正: setIsLoding -> setIsLoading

    // ログインボタンが押された時のアクション
    const handleLogin = async (e) => {
        e.preventDefault(); // 画面の無駄なリロード（デフォルト動作）を防ぐ
        setErrorMessage('');

        // 1. クライアント側の入力バリデーション（空チェック）
        if (!loginId || !password) {
            setErrorMessage('IDとパスワードを入力してください。');
            return;
        }

        setIsLoading(true);

        try {
            // 2. 実際のバックエンドAPIに認証リクエストを送る
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    login_id: loginId,
                    password: password
                }),
            });

            if (response.ok) {
                const data = await response.json();
                console.log("ログイン成功, 発行されたトークン:", data.access_token);
                
                // 3. セッション情報（トークンと講師データ）をブラウザ(LocalStorage)に保存
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('teacher', JSON.stringify(data.teacher));
                
                // 4. 親コンポーネント(App.jsx)にログイン成功を通知し、画面を切り替える
                onLoginSuccess(data.teacher);
            } else {
                // 401エラー（認証失敗）などの処理
                const errorData = await response.json();
                setErrorMessage(errorData.detail || 'IDまたはパスワードが間違っています。');
            }
        } catch (error) {
            console.error('API通信エラー:', error);
            setErrorMessage('サーバとの通信に失敗しました。バックエンドを起動しているか確認してください。');
        } finally {
            setIsLoading(false); // 成功・失敗に関わらずローディング状態を解除
        }
    };

    // UIコンポーネント（Login.jsx）で必要なデータと関数だけを返す
    return {
        loginId, setLoginId,
        password, setPassword,
        errorMessage,
        isLoading,
        handleLogin
    };
}