import { useState, useEffect } from 'react';
import Login from './pages/Login';

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

    return(
        <div>
            {!loggedInTeacher ? (<Login onLoginSuccess={handleLoginSuccess}/>
            ) : (
                <div style={{ padding: '40px', textAlign: 'center', marginTop: '50px'}}>
                    <h1>ログイン成功</h1>
                    <p style={{ fontSize: '20px', color: '#2c3e50', marginTop: '15px'}}>
                        ようこそ, <strong>{loggedInTeacher.name}</strong>先生
                    </p>
                    
                    <p style={{ fontSize: '16px', color: '#7f8c8d', marginTop: '5px'}}>
                        担当クラス: {loggedInTeacher.class_id}組
                    </p>
                    {/*Todo: 成績アラームを受信するdashboardコンポナント */}
                </div> 
            )}
        </div>
    );
}

export default App;
