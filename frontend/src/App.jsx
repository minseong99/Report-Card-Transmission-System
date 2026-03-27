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
        <div style={{padding: '20px', minHeight: '100vh', backgroundColor: '#f4f7f6'}}>
            {!loggedInTeacher ? 
                (<Login onLoginSuccess={handleLoginSuccess}/>
            ) : (
                <div style={{ padding: '40px', textAlign: 'center', marginTop: '50px'}}>
                    <h1>成績表送信システム</h1>
                    {/* logout button */}
                    <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '20px', maxWidth: '800px', margin: '0 auto 20px auto'}}>
                        <button
                            onClick={handleLogout}
                            style={{ padding: '8px 16px', backgroundColor: '#3822c5', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}
                        >
                            ログアウト
                        </button>
                    </div>
                    {/*Todo: 成績アラームを受信するdashboardコンポナント */}
                    <Dashboard teacher={loggedInTeacher}/>
                </div> 
            )}
        </div>
    );
}

export default App;
