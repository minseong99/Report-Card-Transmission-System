import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'; //ルーティング用ライブラリをインポート
import { useAuth } from './hooks/useAuth';
import Header from './components/layout/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

/**
 * ログインしていないユーザーが保護されたページ（ダッシュボードなど）に
 * アクセスしようとした場合、強制的にログイン画面へリダイレクトするコンポーネント
 */
const ProtectedRoute = ({ children, loggedInTeacher }) => {
    if (!loggedInTeacher) {
        return <Navigate to="/login" replace />; // ログイン画面へ弾く
    }
    return children; // 認証済みならそのまま表示
};


/**
 * アプリケーションの最上位コンポーネント (ルート)
 * 認証状態に応じて、表示する画面（Login or Dashboard）を切り替えます。
 */
function App() {
    // 認証ロジックをカスタムフックから呼び出すだけ！
    const { loggedInTeacher, login, logout, isAuthChecking } = useAuth();

    // セッション復元中（F5更新時など）は、一瞬だけローディング画面を見せて
    // ログイン画面がチラつくのを防ぎます。
    if (isAuthChecking) {
        return <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>読み込み中...</div>;
    }

return(
        <Router>
            <div style={{ minHeight: '100vh', backgroundColor: '#f4f7f6', margin: 0, padding: 0 }}>
                
                {/* URLごとの表示ルール(Routes)を定義 */}
                <Routes>
                    
                    {/* ルート1: ログイン画面 (/login) */}
                    <Route 
                        path="/login" 
                        element={
                            // 既にログイン済みの人が /login に来たら、自動でダッシュボード(/)に飛ばす
                            loggedInTeacher ? <Navigate to="/Dashboard" replace /> : <Login onLoginSuccess={login}/>
                        } 
                    />
                    
                    {/* ルート2: メインダッシュボード (/) */}
                    <Route 
                        path="/Dashboard" 
                        element={
                            // ProtectedRoute で包むことで、未ログインのアクセスをブロック
                            <ProtectedRoute loggedInTeacher={loggedInTeacher}>
                                <div style={{ width: '100%' }}>
                                    <Header onLogout={logout} />
                                    <div style={{ padding: '20px' }}>
                                        <Dashboard teacher={loggedInTeacher}/>
                                    </div>
                                </div> 
                            </ProtectedRoute>
                        } 
                    />

                    {/* ルート3: 存在しないURL (404対策) */}
                    <Route 
                        path="*" 
                        element={<Navigate to="/Dashboard" replace />} 
                    />
                    
                </Routes>
                
            </div>
        </Router>
    );
}

export default App;
