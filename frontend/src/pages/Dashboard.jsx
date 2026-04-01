import { useState, useMemo, useRef, useEffect } from 'react';
import './Dashboard.css';

// カスタムフックと分離されたUIコンポーネントをインポート
import { useDashboardData } from '../hooks/useDashboardData';
import { Toast, ConfirmModal, Pagination } from '../components/common/SharedUI';
import StudentTable from '../components/dashboard/StudentTable';
import DraftPreview from '../components/preview/DraftPreview';

/**
 * ダッシュボードのメインViewコンポーネント
 * * 【アーキテクチャのポイント】
 * 1. データ取得やAPI通信などのビジネスロジックは `useDashboardData` フックに完全に委譲しています。
 * 2. このコンポーネントは「UIの状態管理」と「コンポーネントの配置（レイアウト）」のみを担当します。
 * 3. `useMemo` を活用し、不要なレンダリングや配列の再計算を防ぐパフォーマンス最適化を行っています。
 */
export default function Dashboard({ teacher }) {
    // ==========================================
    // 1. データとビジネスロジックの取得 (Custom Hook)
    // ==========================================
    const { 
        alarms,             // 新着アラームのリスト
        studentsData,       // 担当クラスの全生徒の成績データ
        currentExamDate,    // 最新の試験実施日
        updateStudentSuccess, // 個別成績表の生成成功時の状態更新関数
        sendBatchReports,    // 一括送信APIを呼び出す関数
        refreshStudentsData,  // 点数Update
        smartModalData, setSmartModalData, generateClassReports, isBulkGenerating
    } = useDashboardData(teacher.class_id);

    // ==========================================
    // 2. UIのローカル状態管理 (Local State)
    // ==========================================
    const [activeTab, setActiveTab] = useState('pending'); // 現在選択中のタブ ('pending' | 'completed')
    const [currentPage, setCurrentPage] = useState(1);     // ページネーションの現在ページ
    const [selectedStudent, setSelectedStudent] = useState(null); // プレビュー表示中の生徒データ
    const [showConfirmModal, setShowConfirmModal] = useState(false); // 一括送信の確認モーダル表示フラグ
    const [toastMessage, setToastMessage] = useState("");  // トースト通知のメッセージ内容

    const itemsPerPage = 10; // 1ページあたりの表示件数

    const prevGenerating = useRef(isBulkGenerating); // 以前Loading状態記憶

    useEffect(() => {
        if(prevGenerating.current === true && isBulkGenerating === false){
            setActiveTab('completed')
        }
        prevGenerating.current = isBulkGenerating;
    }, [isBulkGenerating]);

    /**
     * トースト通知を画面下部に表示し、3秒後に自動で消すヘルパー関数
     */
    const showToast = (message) => {
        setToastMessage(message);
        setTimeout(() => setToastMessage(""), 3000);
    };

    // ==========================================
    // 3. パフォーマンス最適化 (useMemoによる派生状態の計算)
    // ==========================================
    // studentsData, activeTab, currentPage のいずれかが変化した時のみ再計算される
    const { 
        currentDisplayList, // 現在のページで実際に表示する10件のデータ
        completedStudents,  // 「送信待機中(完了)」ステータスの全生徒
        pendingCount,       // 「未確認(保留)」ステータスの生徒数
        totalPages,         // ページネーションの総ページ数
        startIndex          // 現在のページの最初のインデックス（No.の計算用）
    } = useMemo(() => {
        // 1. データのフィルタリング
        const pending = studentsData.filter(s => s.status !== '完了' && s.status !== '送信済');
        const completed = studentsData.filter(s => s.status === '完了');
        
        // 2. 現在のタブに応じたリストの選択
        const list = activeTab === 'pending' ? pending : completed;
        
        // 3. ページネーションの計算
        const start = (currentPage - 1) * itemsPerPage;
        
        return {
            currentDisplayList: list.slice(start, start + itemsPerPage),
            completedStudents: completed,
            pendingCount: pending.length,
            totalPages: Math.ceil(list.length / itemsPerPage) || 1,
            startIndex: start
        };
    }, [studentsData, activeTab, currentPage]);

    // ==========================================
    // 4. イベントハンドラー (UI Action)
    // ==========================================
    
    /**
     * タブを切り替えた際に、ページを1ページ目にリセットする
     */
    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setCurrentPage(1);
    };


    /**
     * 一括送信のアクション
     * モーダルでの確認後、実際の通信処理はHookに委譲し、結果に応じてUI（トースト通知）を制御します。
     */
    const executeBatchSend = () => {
        console.log("[Dashboard] 一括送信処理を開始します。");
        setShowConfirmModal(false); // 確認モーダルを閉じる
        
        const studentIds = completedStudents.map(s => s.studentId);
        console.log("[Dashboard] 送信対象の生徒IDリスト:", studentIds);
        console.log("[Dashboard] 対象の試験実施日:", currentExamDate);

        // 安全装置: Hookから関数が正しく取得できているか確認
        if (typeof sendBatchReports !== 'function') {
            alert("フロントエンドエラー: sendBatchReports 関数が見つかりません。useDashboardData.js との連携を確認してください。");
            return;
        }

        // 実際のバックエンド通信処理を実行 (ロジックはHook内)
        sendBatchReports(
            studentIds, 
            currentExamDate,
            // 成功時のコールバック (onSuccess)
            (count) => {
                console.log("[Dashboard] 通信成功コールバックを実行しました。");
                showToast(`${count}名の保護者へ送信を完了しました。`);
            },
            // 失敗・エラー時のコールバック (onError)
            (errorMsg) => {
                console.error("[Dashboard] エラーコールバックを実行しました:", errorMsg);
                showToast(`${errorMsg}`);
            }
        );
    };

    // ==========================================
    // 5. 画面のレンダリング (View)
    // ==========================================
    return (
        <div className="dashboard-container">
            {/* ---------------- 全体画面Loading overlay ---------------- */}
            {isBulkGenerating && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
                    backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(8px)',
                    display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
                    zIndex: 10000, 
                    cursor: 'wait'
                }}>
                    <div className="loading-spinner" style={{
                        width: '50px', height: '50px', border: '5px solid #e2e8f0',
                        borderTop: '5px solid #3b82f6', borderRadius: '50%',
                        animation: 'spin 1s linear infinite', marginBottom: '20px'
                    }}></div>
                    <h2 style={{ color: '#1e293b', margin: '0' }}>成績表生成中。。。</h2>
                    <p style={{ color: '#64748b', marginTop: '10px' }}>
                        {teacher.class_id}組学生たちの生成表を生成しています。お待ちしてください。
                    </p>
                    
                    <style>{`
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                    `}</style>
                </div>
            )}
            {/* ---------------- ヘッダー領域 ---------------- */}
            <header className="dashboard-header" style={{ opacity: isBulkGenerating ? 0.5 : 1}}>
                <div className="header-left">
                    <h2>{teacher.name} 先生のワークスペース</h2>
                    <span className="class-badge">担当: {teacher.class_id}組</span>
                </div>
                <div className="header-right">
                    <span className="live-status"><span className="dot"></span> システム同期中</span>
                </div>
            </header>

            <main className="dashboard-layout" style={{ 
                        // 採点完了モーダルがある時裏側をblur処理
                        filter: (smartModalData || isBulkGenerating) ? 'blur(50px) grayscale(50%)' : 'none', 
                        transition: 'filter 0.3s ease',
                        pointerEvents: isBulkGenerating ? 'none' : 'auto'  // 裏側クリック防ぐ
                }}>
                {/* ---------------- 左側: アラームサイドバー ---------------- */}
                
                <aside className="sidebar" >
                    <section className="status-card">
                        <h3>アラーム</h3>
                        <div className="alarm-list">
                            {alarms.length === 0 ? (
                                <div className="no-data">現在、アラームがありません。</div>
                            ) : (
                                alarms.map((alarm) => (
                                    <div key={alarm.id} className={`alert-box ${alarm.type}`}>
                                        <strong>{alarm.message}</strong>
                                        <p>成績表草案を確認して生成してください。</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>
                </aside>

                {/* ---------------- 右側: メインコンテンツ領域 ---------------- */}
                <section className="main-content">
                    <div className="content-header">
                        <h3>
                            {activeTab === 'completed' ? '成績表送信待機中一覧' : '成績草案一覧'}
                            {currentExamDate && `(${currentExamDate} 実施)`}
                        </h3>
                        
                        {/* 完了タブの時のみ、一括送信ボタンを表示 */}
                        {activeTab === 'completed' && (
                            <button 
                                className="btn-primary" 
                                onClick={() => setShowConfirmModal(true)}
                                disabled={completedStudents.length === 0}
                                style={{ 
                                    backgroundColor: completedStudents.length === 0 ? '#cbd5e1' : '#3b82f6', 
                                    color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', 
                                    fontWeight: 'bold', transition: '0.2s',
                                    cursor: completedStudents.length === 0 ? 'not-allowed' : 'pointer'
                                }}
                            >
                                保護者へ一括送信
                            </button>
                        )}
                    </div>
                    
                    {/* データが1件もない場合の空状態（Empty State） */}
                    {studentsData.length === 0 ? (
                        <div className="placeholder-area">
                            <div className="empty-state">
                                <span className="icon">📊</span>
                                <h4>最近25日以内の成績データがありません</h4>
                            </div>
                        </div>
                    ) : (
                        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
                            
                            {/* タブナビゲーション */}
                            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                                <button 
                                    onClick={() => handleTabChange('pending')} 
                                    style={{ padding: '10px 20px', backgroundColor: activeTab === 'pending' ? '#e74c3c' : '#f1f5f9', color: activeTab === 'pending' ? 'white' : '#64748b', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                                >
                                    未確認・処理待ち ({pendingCount})
                                </button>
                                <button 
                                    onClick={() => handleTabChange('completed')} 
                                    style={{ padding: '10px 20px', backgroundColor: activeTab === 'completed' ? '#10b981' : '#f1f5f9', color: activeTab === 'completed' ? 'white' : '#64748b', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                                >
                                    成績表生成完了 ({completedStudents.length})
                                </button>
                            </div>

                            {/* テーブルコンポーネント (純粋なUI描画のみを担当) */}
                            <div style={{ flexGrow: 1, overflowY: 'auto' }}>
                                <StudentTable 
                                    list={currentDisplayList} 
                                    activeTab={activeTab} 
                                    startIndex={startIndex} 
                                    onPreviewClick={setSelectedStudent} 
                                />
                            </div>

                            {/* ページネーションコンポーネント */}
                            {studentsData.length > 0 && (
                                <Pagination 
                                    currentPage={currentPage} 
                                    totalPages={totalPages} 
                                    onPageChange={setCurrentPage} 
                                />
                            )}
                        </div>
                    )}
                </section>
            </main>
            {smartModalData && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
                    backgroundColor: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)',
                    display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999,
                    animation: 'fadeIn 0.3s ease-out'
                }}>
                    <div style={{
                        backgroundColor: 'white', padding: '30px 40px', borderRadius: '16px',
                        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                        width: '500px', maxWidth: '90%', textAlign: 'center'
                    }}>
                        <h2 style={{ margin: '0 0 15px 0', color: '#1e293b', fontSize: '22px' }}>
                            採点がすべて完了しました！
                        </h2>
                        <p style={{ color: '#475569', fontSize: '15px', lineHeight: '1.6', marginBottom: '30px' }}>
                            {smartModalData.examDate}実施分のデータ入力が完了しました。<br/>
                            システムが分析したデータを利用して、<br/>
                            <strong>担当クラス全員の成績表を全自動で生成</strong>しますか？
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {/* Primary Action: 一括自動生成 */}
                            <button 
                                onClick={() => {
                                    generateClassReports(
                                        smartModalData.examDate,
                                        (msg) => { showToast(`${msg}`); setSmartModalData(null); },
                                        (err) => { showToast(`${err}`); setSmartModalData(null); }
                                    );
                                }}
                                style={{
                                    backgroundColor: '#3b82f6', color: 'white', padding: '14px',
                                    borderRadius: '8px', border: 'none', fontSize: '15px', fontWeight: 'bold',
                                    cursor: 'pointer', boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)',
                                    transition: 'transform 0.1s'
                                }}
                                onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
                                onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
                            >
                                はい、クラス全員分を1秒で自動生成する 
                            </button>

                            {/* Secondary Action */}
                            <button 
                                onClick={() => {
                                    setSmartModalData(null); 
                                    handleTabChange('pending');
                                }}
                                style={{
                                    backgroundColor: 'white', color: '#64748b', padding: '12px',
                                    borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', fontWeight: 'bold',
                                    cursor: 'pointer', transition: 'background-color 0.2s'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                            >
                                いいえ、個別に確認・修正してから生成する
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* ---------------- ポップアップ＆モーダル領域 ---------------- */}
            
            {/* 個別成績表のプレビュー＆編集モーダル */}
            {selectedStudent && (
                <DraftPreview 
                    studentData={selectedStudent} 
                    examDate={currentExamDate}
                    onClose={() => setSelectedStudent(null)}
                    onSuccess={(id, url) => {
                        updateStudentSuccess(id, url); // Hookの関数で状態を「完了」に更新
                        setSelectedStudent(null);      // モーダルを閉じる
                    }}
                    onScoreUpdated={(freshData) => {
                        refreshStudentsData(freshData);
                        const updatedSelected = freshData.find(s => s.studentId === selectedStudent.studentId);
                        setSelectedStudent(updatedSelected);
                    }}  
                />
            )}

            {/* 一括送信の最終確認モーダル */}
            <ConfirmModal 
                isOpen={showConfirmModal} 
                title="一括送信の確認" 
                onConfirm={executeBatchSend} 
                onCancel={() => setShowConfirmModal(false)} 
                confirmText="はい、送信します"
            >
                <strong>{completedStudents.length}名</strong>の保護者に成績表を一括送信しますか？<br/>
                <span style={{ fontSize: '12px', color: '#e74c3c' }}>※この操作は取り消せません。</span>
            </ConfirmModal>

            {/* 画面下部のトースト通知 */}
            <Toast message={toastMessage} />
        </div>
    );
}