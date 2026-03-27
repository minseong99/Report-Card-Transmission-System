import { useState } from 'react';
import Login from './pages/Login';

function App() {
    // 現在ログインしている講師ID
    const [loggedInTeacher, setLoggedInTeacher] = useState(null);

    const handleLoginSuccess = (teacerData) => {
        setLoggedInTeacher(teacerData);
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
