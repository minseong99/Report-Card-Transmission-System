import { useState, useEffect } from 'react';

/**
 * ダッシュボードのデータ取得と状態管理を行うカスタムフック
 * API通信（ポーリング含む）やデータ加工のビジネスロジックをここに集約し、UIコンポーネントをクリーンに保ちます。
 */
export function useDashboardData(class_id) {
    const [alarms, setAlarms] = useState([]);
    const [studentsData, setStudentsData] = useState([]);
    const [currentExamDate, setCurrentExamDate] = useState(null);

    // 401エラー共通処理
    const handleAuthError = (status) => {
        if (status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
            return true;
        }
        return false;
    };

    // 1. アラームのポーリング (30秒間隔)
    useEffect(() => {
        if (!class_id) return;

        const checkStatus = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/notification?t=${new Date().getTime()}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Cache-Control': 'no-cache'
                    },
                    cache: 'no-store'
                });

                if (response.ok) {
                    const data = await response.json();
                    setAlarms(data.alerts);
                } else if (!handleAuthError(response.status)) {
                    console.error("サーバ側エラー:", response.status);
                }
            } catch (error) {
                console.error("アラーム通信エラー:", error);
            }
        };

        const intervalID = setInterval(checkStatus, 30000);
        checkStatus();
        
        return () => clearInterval(intervalID);    
    }, [class_id]);

    // 2. 成績草案データの取得 (アラーム数が変化した時のみ)
    useEffect(() => {
        if (!class_id) return;

        const fetchDrafts = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/drafts/preview?t=${new Date().getTime()}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Cache-Control': 'no-cache'
                    },
                    cache: 'no-store'
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.data) {
                        setStudentsData(result.data);
                        setCurrentExamDate(result.exam_date);
                    }
                } else if (!handleAuthError(response.status)) {
                    const errorData = await response.json();
                    alert(`エラーが発生しました: ${errorData.detail || '不明なエラー'}`);
                }
            } catch (error) {
                console.error("プレビューデータ取得エラー:", error);
            }
        };
        fetchDrafts();
    }, [class_id, alarms.length]);

    // 3. 個別の成績表生成・確認成功時のアクション
    const updateStudentSuccess = (studentId, fileUrl) => {
        setStudentsData(prevData => 
            prevData.map(student => 
                student.studentId === studentId
                    ? { ...student, status: '完了', fileUrl: fileUrl }
                    : student
            )
        );
    };

    /**
     * 4. 一括送信のAPI呼び出しと状態更新ロジック
     * @param {Array<number>} studentIds - 送信対象の生徒IDリスト
     * @param {string} examDate - 試験実施日
     * @param {Function} onSuccess - 成功時にUI側で実行されるコールバック
     * @param {Function} onError - 失敗時にUI側で実行されるコールバック
     */
    const sendBatchReports = async (studentIds, examDate, onSuccess, onError) => {
        console.log("[Hook] バックエンドへAPIリクエストを送信します:", { studentIds, examDate });
        try {
            const response = await fetch('http://localhost:8000/api/reports/send-batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ student_ids: studentIds, exam_date: examDate })
            });

            console.log("[Hook] バックエンドから応答を受信しました。ステータスコード:", response.status);

            if (response.ok) {
                // 通信成功時: UIの再レンダリングのために内部Stateを「送信済」に更新
                setStudentsData(prevData => 
                    prevData.map(student => 
                        studentIds.includes(student.studentId) 
                            ? { ...student, status: '送信済' } 
                            : student
                    )
                );
                // Dashboard.jsx に成功した人数を伝えてトーストを表示させる
                onSuccess(studentIds.length);
            } else {
                // 認証エラー(401)の場合は共通処理でログアウト画面へ
                if (handleAuthError(response.status)) return;
                
                // その他のサーバーエラー
                onError("送信に失敗しました。(サーバー応答エラー)");
            }
        } catch (error) {
            console.error("[Hook] 通信エラー詳細:", error);
            // ネットワーク切断やCORSエラーなどの例外処理
            onError("ネットワークエラーが発生しました。(通信エラー)");
        }
    };
    // 点数修正後、サーバから受けた最新情報と更新する
    const refreshStudentsData = (freshData) => {
        setStudentsData(freshData);
    };


    // UIで使うものだけをスッキリと返す
    return {
        alarms,
        studentsData,
        currentExamDate,
        updateStudentSuccess,
        sendBatchReports,
        refreshStudentsData
    };
}