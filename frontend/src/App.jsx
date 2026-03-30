import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

function App() {
    // 現在ログインしている講師ID
    const [loggedInTeacher, setLoggedInTeacher] = useState(null);

    // login session 維持
    useEffect(() => {
        const savedTeacher = localStorage.getItem('teacher');
        const token = localStorage.getItem('token');

        if (savedTeacher && token) {
            try {
                const teacherData = JSON.parse(savedTeacher);
                setLoggedInTeacher(teacherData);
            }catch (error) {
                console.log("local storage data parsing error: ", error);
            }
        }
    }, []); // 最小のレンダリングに一度だけ実行する

    const handleLoginSuccess = (teacherData) => {
        setLoggedInTeacher(teacherData);
    }

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('teacher');
        setLoggedInTeacher(null);
    }

return(
        <div style={{ minHeight: '100vh', backgroundColor: '#f4f7f6', margin: 0, padding: 0 }}>
            {!loggedInTeacher ? 
                (<Login onLoginSuccess={handleLoginSuccess}/>
            ) : (
                <div style={{ width: '100%' }}>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '15px 30px', backgroundColor: 'white', borderBottom: '1px solid #e2e8f0' }}>
                        <h1 style={{ margin: 0, fontSize: '22px', color: '#1e293b' }}>成績表送信システム</h1>
                        
                        {/* logout button */}
                        <button
                            onClick={handleLogout}
                            style={{ padding: '8px 16px', backgroundColor: '#7f7d8e', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold', transition: '0.2s' }}
                        >
                            ログアウト
                        </button>
                    </div>

                    {/*成績アラームを受信するdashboardコンポナント */}
                    <div style={{ padding: '20px' }}>
                        <Dashboard teacher={loggedInTeacher}/>
                    </div>
                </div> 
            )}
        </div>
    );
}

export default App;
