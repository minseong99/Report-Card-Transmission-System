import { useState } from 'react';
import Login from './pages/Login';

function App() {
    // 現在ログインしている講師ID
    const [loggedInTeacherId, setLoggedInTeacherId] = useState(null);

    const handleLoginSuccess = (teacerId) => {
        setLoggedInTeacherId(teacerId);
    }

    return(
        <div>
            {!loggedInTeacherId ? (<Login onLoginSuccess={handleLoginSuccess}/>
            ) : (
                <div style={{ padding: '20px', textAlign: 'center', marginTop: '50px'}}>
                    <h1>ログイン成功</h1>
                    <p>ようこそ, {loggedInTeacherId}先生</p>
                    {/*To do: dashboardコンポナント */}
                </div> 
            )}
        </div>
    );
}

export default App;
