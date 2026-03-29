import {useState, useEffect} from 'react';
import './Dashboard.css';
import DraftPreview from './DraftPreview';

export default function Dashboard({teacher}) {
    const [alarms, setAlarms] = useState([]);
    
    const [studentsData, setStudentsData] = useState([]);
    const [currentExamDate, setCurrentExamDate] = useState(null);
    const [selectedStudent, setSelectedStudent] = useState(null);

    // Tab, Pagination state
    const [activeTab, setActiveTab] = useState('pending'); // 'pending' または 'completed'
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10; 

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
        const intervalID = setInterval(checkStatus, 3000); //３秒ごと
        checkStatus(); 
        // ログアウトしたり、画面を閉じたら監視停止
        return () => clearInterval(intervalID);    
    }, [teacher.class_id]);

useEffect(() => {
        const fetchDrafts = async () => {
            try {
                // Cache-bursting 
                const response = await fetch(`http://localhost:8000/api/drafts/preview/${teacher.class_id}?t=${new Date().getTime()}`,{
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Cache-Control': 'no-cache'
                    },
                    cache: 'no-store'
                });
                if(response.ok) {
                    const result = await response.json();
                    if (result.data) {
                        setStudentsData(result.data);
                        setCurrentExamDate(result.exam_date);
                    }
                }

            } catch (error) {
                console.error("プレビューデータ取得エラー", error);
            }
        };
        fetchDrafts();
    }, [teacher.class_id, alarms]);
    
    // データ分離
    const pendingStudents = studentsData.filter(s => s.status !== '完了');
    const completedStudents = studentsData.filter(s => s.status === '完了');

    // 現在洗濯されたTABの全体リスト
    const currentList = activeTab === 'pending' ? pendingStudents : completedStudents;

    // pagination計算
    const totalPages = Math.ceil(currentList.length / itemsPerPage) || 1;
    const startIndex = (currentPage - 1) * itemsPerPage;
    const currentDisplayList = currentList.slice(startIndex, startIndex + itemsPerPage);

    // Tabが変更されたら1に初期化
    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setCurrentPage(1);
    };

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div className="header-left">
                    <h2>{teacher.name} 先生のワークスペース</h2>
                    <span className="class-badge">担当: {teacher.class_id}組</span>
                </div>
                <div className="header-right">
                    <span className="live-status"><span className="dot"></span> システム同期中</span>
                </div>
            </header>

            <main className="dashboard-layout">
                {/* 左側 */}
                <aside className="sidebar">
                    <section className="status-card">
                        <h3>クラスステータス</h3>
                        <div className="alarm-list">
                            {alarms.length === 0 ? (
                                <div className="no-data">現在、処理中のデータはありません。</div>
                            ) : (
                                alarms.map((alarm) => (
                                    <div key={alarm.id} className={`alert-box ${alarm.type}`}>
                                        <strong>{alarm.message}</strong>
                                        <p>成績表草案を確認して成績表を生成してください。</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>
                </aside>

                {/* 右側 */}
                <section className="main-content">
                    <div className="content-header">
                        <h3>{activeTab === 'completed' ? '成績表送信待機中一覧' : '成績草案一覧'}{currentExamDate && `(${currentExamDate} 実施)`}</h3>
                        
                        {activeTab === 'completed' && (
                            <button 
                                className="btn-primary" 
                                disabled={completedStudents.length === 0}
                                style={{
                                    backgroundColor: completedStudents.length === 0 ? '#cbd5e1' : '#3b82f6', // 활성화 시 파란색으로 강조
                                    color: 'white',
                                    border: 'none',
                                    padding: '8px 16px',
                                    borderRadius: '6px',
                                    fontWeight: 'bold',
                                    cursor: completedStudents.length === 0 ? 'not-allowed' : 'pointer',
                                    transition: '0.2s'
                                }}
                            >
                                保護者へ一括送信
                            </button>
                        )}
                    </div>
                    
                    {studentsData.length === 0 ? (
                        <div className="placeholder-area">
                            <div className="empty-state">
                                <span className="icon">📊</span>
                                <h4>最近25日以内の成績データがありません</h4>
                                <p>OMRスキャンが完了するとここに生徒の一覧が表示されます。</p>
                            </div>
                        </div>
                    ) : (
                        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
                            
                            {/* Tabボタン */}
                            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                                <button
                                    onClick={() => handleTabChange('pending')}
                                    style={{
                                        padding: '10px 20px',
                                        backgroundColor: activeTab === 'pending' ? '#e74c3c' : '#f1f5f9',
                                        color: activeTab === 'pending' ? 'white' : '#64748b',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        fontWeight: 'bold',
                                        transition: '0.2s'
                                    }}
                                >
                                    未確認・処理待ち ({pendingStudents.length})
                                </button>
                                <button
                                    onClick={() => handleTabChange('completed')}
                                    style={{
                                        padding: '10px 20px',
                                        backgroundColor: activeTab === 'completed' ? '#10b981' : '#f1f5f9',
                                        color: activeTab === 'completed' ? 'white' : '#64748b',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        fontWeight: 'bold',
                                        transition: '0.2s'
                                    }}
                                >
                                    成績表生成完了・送信待機中 ({completedStudents.length})
                                </button>
                            </div>

                            {/* 統合したテーブル領域 */}
                            <div style={{ flexGrow: 1, overflowY: 'auto' }}>
                                {currentList.length === 0 ? (
                                    <div style={{ padding: '40px 20px', textAlign: 'center', color: '#94a3b8', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
                                        {activeTab === 'pending' ? '未処理の生徒はいません。' : '完了した生徒はまだいません。'}
                                    </div>
                                ) : (
                                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', opacity: activeTab === 'completed' ? 0.8 : 1 }}>
                                        <thead style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                                            <tr>
                                                <th style={{ padding: '12px', width: '50px' }}>No.</th>
                                                <th style={{ padding: '12px' }}>生徒名</th>
                                                <th style={{ padding: '12px' }}>総点</th>
                                                <th style={{ padding: '12px' }}>クラス順位</th>
                                                <th style={{ padding: '12px' }}>全校順位</th>
                                                <th style={{ padding: '12px', textAlign: 'center' }}>
                                                    {activeTab === 'pending' ? 'アクション' : 'ステータス'}
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {currentDisplayList.map((student, index) => (
                                                <tr key={student.studentId} style={{ borderBottom: '1px solid #f1f5f9', backgroundColor: activeTab === 'completed' ? '#f8fafc' : 'white' }}>
                                                    {/* 番号 */}
                                                    <td style={{ padding: '12px', color: '#94a3b8', fontWeight: 'bold' }}>
                                                        {startIndex + index + 1}
                                                    </td>
                                                    <td style={{ padding: '12px', fontWeight: 'bold', color: activeTab === 'completed' ? '#64748b' : '#333' }}>
                                                        {student.studentName}
                                                    </td>
                                                    <td style={{ padding: '12px', color: activeTab === 'completed' ? '#64748b' : '#333' }}>
                                                        {student.totalScore}点
                                                    </td>
                                                    <td style={{ padding: '12px', fontWeight: 'bold', color: activeTab === 'pending' ? '#e74c3c' : '#64748b' }}>
                                                        {student.classRank}位
                                                    </td>
                                                    <td style={{ padding: '12px', color: activeTab === 'completed' ? '#64748b' : '#333' }}>
                                                        {student.overallRank}位
                                                    </td>
                                                    <td style={{ padding: '12px', textAlign: 'center' }}>
                                                        
                                                        {activeTab === 'pending' ? (
                                                            <button 
                                                                style={{ padding: '6px 12px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                                                                onClick={() => setSelectedStudent(student)}
                                                            >
                                                                プレビュー確認
                                                            </button>
                                                        ) : (
                                                            <span style={{ padding: '6px 12px', backgroundColor: '#e2e8f0', color: '#64748b', borderRadius: '4px', fontSize: '13px', fontWeight: 'bold' }}>
                                                                確認済
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>

                            {/* pagination control*/}
                            {currentList.length > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e2e8f0', gap: '15px' }}>
                                    <button 
                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                        disabled={currentPage === 1}
                                        style={{ padding: '8px 16px', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: currentPage === 1 ? '#f8fafc' : 'white', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', color: '#475569', fontWeight: 'bold' }}
                                    >
                                        前へ
                                    </button>
                                    <span style={{ color: '#64748b', fontWeight: 'bold', fontSize: '14px' }}>
                                        {currentPage} / {totalPages} ページ
                                    </span>
                                    <button 
                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                        disabled={currentPage === totalPages}
                                        style={{ padding: '8px 16px', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: currentPage === totalPages ? '#f8fafc' : 'white', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer', color: '#475569', fontWeight: 'bold' }}
                                    >
                                        次へ
                                    </button>
                                </div>
                            )}

                        </div>
                    )}
                </section>
            </main>

            {selectedStudent && (
                <DraftPreview 
                    studentData={selectedStudent} 
                    onClose={() => setSelectedStudent(null)} 
                />
            )}
        </div>
    );
}