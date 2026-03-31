import React from 'react';
import { useAuth } from './hooks/useAuth';
import Header from './components/layout/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

/**
 * アプリケーションの最上位コンポーネント (ルート)
 * 認証状態に応じて、表示する画面（Login or Dashboard）を切り替えます。
 */
function App() {
    // 認証ロジックをカスタムフックから呼び出すだけ！
    const { loggedInTeacher, login, logout } = useAuth();

    return(
        <div style={{ minHeight: '100vh', backgroundColor: '#f4f7f6', margin: 0, padding: 0 }}>
            {/* 未ログイン状態：ログイン画面を表示 */}
            {!loggedInTeacher ? (
                <Login onLoginSuccess={login} />
            ) : (
            /* ログイン済み状態：メイン画面（ダッシュボード）を表示 */
                <div style={{ width: '100%' }}>
                    
                    {/* 分離したヘッダーコンポーネント */}
                    <Header onLogout={logout} />

                    {/* 成績アラームを受信・表示するメイン領域 */}
                    <div style={{ padding: '20px' }}>
                        <Dashboard teacher={loggedInTeacher} />
                    </div>
                    
                </div> 
            )}
        </div>
    );
}

export default App;
