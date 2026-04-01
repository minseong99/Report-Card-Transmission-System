import { useState } from 'react';

/**
 * プレビュー画面の入力状態とAPI通信（成績表生成・点数修正）を管理するカスタムフック
 */
export function useDraftPreview(studentData, examDate, onSuccess, onScoreUpdated) {
    // 編集可能なテキストエリアの状態
    const [comment, setComment] = useState("\n各科目でバランスよく得点できています。特に英語の伸びが顕著です。次回の模試に向けて数学の応用問題に注力しましょう。");
    const [university, setUniversity] = useState("東京大学 理科一類 (B判定)\n早稲田大学 基幹理工学部 (A判定)");
    
    // 生成中のローディング状態
    const [isGenerating, setIsGenerating] = useState(false);

    // 点数修正の状態
    const [isEditMode, setIsEditMode] = useState(false);
    const [editScores, setEditScores] = useState({});
    const [isUpdatingScore, setIsUpdatingScore] = useState(false);

    // 編集モードOn-OFF切り替え
    const toggleEditMode = () => {
        if(!isEditMode) {
            // 編集モードに入る時、現在の点数を初期値としてセット
            const initialScores = {};
            studentData.currentScores.forEach(s => {
                initialScores[s.subject] = s.score;
            });
            setEditScores(initialScores);
        }
        setIsEditMode(!isEditMode);
    }
    // 点数入力ハンドラー
    const handleScoreChange = (subject, value) => {
        setEditScores(prev => ({ ...prev, [subject]: value}));
    };

    // 点数の修正をバッグエンドに送信するAPI通信ロジック
    const handleScoreUpdate = async () => {
        //空欄や不正な文字がないかチェック
        const hasInvalidScore = Object.values(editScores).some(val => val === "" || isNaN(val) || val < 0 || val > 100);
        if(hasInvalidScore){
            // alert대신 모달로 경고문
            return;
        }

        setIsUpdatingScore(true);
        try{
            // 文字列になっている可能性があるので数値に変換
            const parseScores = {};
            for (const [subj, val] of Object.entries(editScores)) {
                parseScores[subj] = parseInt(val, 10);
            }

            const response = await fetch('http://localhost:8000/api/drafts/update-score', {
                method: 'PUT',
                headers:{
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    score_id: studentData.score_id,
                    exam_date: examDate,
                    class_id: studentData.class_id,
                    updated_scores: parseScores
                })
            });
            if (response.ok){
                const result = await response.json();
                if (onScoreUpdated) {
                    onScoreUpdated(result.fresh_data);
                }
                setIsEditMode(false);
            } else {
                const errorData = await response.json().catch(() => ({}));
                if(response.status === 401) {
                    localStorage.removeItem('token');
                    window.location.href = '/login';
                } else {
                    // modal로 경고문 대체
                }
            }
        } catch (error) {
            console.error("Score update error:", error);
            // modal로 경고문 대체
        }finally {
            setIsUpdatingScore(false);
        }
    } 

    // 最終生成APIの呼び出し
    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            const response = await fetch ('http://localhost:8000/api/reports/confirm', {
                method:'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    student_id: studentData.studentId,
                    exam_date: examDate,
                    comment: comment,
                    university: university
                })
            });

            if (response.ok) {
                const result = await response.json();
                // 成功したら親(Dashboard)に通知してモーダルを閉じる
                onSuccess(studentData.studentId, result.file_url);
            } else {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    window.location.href = '/login';
                } else {
                    const errorData = await response.json();
                    // modal로 대체
                    // alert(`エラーが発生しました: ${errorData.detail || '不明なエラー'}`);
                }
            }  
        } catch (error) {
            console.error("API 通信エラー", error);
            // modal로대체
            // alert("ネットワークエラーが発生しました。");
        } finally {
            setIsGenerating(false);
        }
    };

    return {
        comment, setComment,
        university, setUniversity,
        isGenerating,handleGenerate,
        isEditMode, toggleEditMode, editScores, handleScoreChange, handleScoreUpdate, isUpdatingScore
    };
}