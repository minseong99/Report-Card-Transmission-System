import {useState, useEffect} from 'react';
import './Dashboard.css';

export default function Dashboard({teacher}) {
    const [alarms, setAlarms] = useState([]);

    // polling : 3秒ごとにバッググラウンドを自動監視
    useEffect(() => {
        const checkStatus = async () => {
            try {
                // cache-bursting 適用　： 毎回のrequestが新しいもののようにする方法
                const response = await fetch(`
                    http://localhost:8000/api/notification/${teacher.class_id}?t=${new Date().getTime()}`, 
                    {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Cache-Control': 'no-cache' // cacne使用x
                    }, 
                    cache: 'no-store' // browser cache 無視
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    setAlarms(data.alerts);

                } else {
                    console.log("サーバ側:", response.status)
                }
            }catch (error) {
                console.error("scanner通信エラー:", error);
            }
        };
        const intervalID = setInterval(checkStatus, 60000); //１分ごと
        checkStatus(); 
        // ログアウトしたり、画面を閉じたら監視停止
        return () => clearInterval(intervalID);    
    }, [teacher.class_id]);


    return (
        <div className="dashboard-container">
            {/* top-header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <h2>{teacher.name} 先生のワークスペース</h2>
                    <span className="class-badge">担当: {teacher.class_id}組</span>
                </div>
                <div className="header-right">
                    <span className="live-status">
                        <span className="dot"></span> 採点完了を監視中
                    </span>
                </div>
            </header>

            <main className="dashboard-layout">
                {/* 左側: 通知＆ステータス  */}
                <aside className="sidebar">
                    <section className="status-card">
                        <h3>学生成績表のステータス</h3>
                        <div className="alarm-list">
                            {alarms.length === 0 ? (
                                <div className="no-data">現在、処理中のデータはありません。</div>
                            ) : (
                                alarms.map((alarm) => (
                                    <div key={alarm.id} className={`alert-box ${alarm.type}`}>
                                        <strong>{alarm.message}</strong>
                                        <p>自動生成が終わるまでお待ちください...</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>
                </aside>

                {/* 右側: 成績表メインエリア  */}
                <section className="main-content">
                    <div className="content-header">
                        <h3>成績表一覧 (準備中)</h3>
                        <button className="btn-primary" disabled>一括送信</button>
                    </div>
                    
                    <div className="placeholder-area">
                        <div className="empty-state">
                            <span className="icon">📊</span>
                            <h4>成績データがありません</h4>
                            <p>OMRスキャンが完了し、AIによる草案生成が終わるとここに生徒の成績表が表示されます。</p>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );

}