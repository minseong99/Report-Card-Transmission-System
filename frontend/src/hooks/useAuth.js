import { useState, useEffect } from 'react';

/**
 * アプリケーション全体の認証（ログイン状態）を管理するカスタムフック
 * LocalStorageの読み書きや、ログイン・ログアウトのアクションをカプセル化します。
 */
export function useAuth() {
    // 現在ログインしている講師情報
    const [loggedInTeacher, setLoggedInTeacher] = useState(null);
    const [isAuthChecking, setIsAuthChecking] = useState(true); // セッション確認中の状態

    // 初回マウント時にセッション（ログイン状態）を復元
    useEffect(() => {
        const savedTeacher = localStorage.getItem('teacher');
        const token = localStorage.getItem('token');

        if (savedTeacher && token) {
            try {
                const teacherData = JSON.parse(savedTeacher);
                setLoggedInTeacher(teacherData);
            } catch (error) {
                console.error("Local storage data parsing error: ", error);
            }
        }
        setIsAuthChecking(false); // 確認が完了したらローディング状態を解除
    }, []); // 依存配列が空なので、アプリ起動時に一度だけ実行される

    // ログイン成功時の処理
    const login = (teacherData) => {
        setLoggedInTeacher(teacherData);
    };

    // ログアウト時の処理
    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('teacher');
        setLoggedInTeacher(null);
        // 必要であればここで window.location.href = '/login' を追加してもOK
    };

    return {
        loggedInTeacher,
        isAuthChecking,
        login,
        logout
    };
}