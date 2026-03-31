import { useState } from 'react';

/**
 * プレビュー画面の入力状態とAPI通信（成績表生成）を管理するカスタムフック
 */
export function useDraftPreview(studentData, examDate, onSuccess) {
    // 編集可能なテキストエリアの状態
    const [comment, setComment] = useState("\n各科目でバランスよく得点できています。特に英語の伸びが顕著です。次回の模試に向けて数学の応用問題に注力しましょう。");
    const [university, setUniversity] = useState("東京大学 理科一類 (B判定)\n早稲田大学 基幹理工学部 (A判定)");
    
    // 生成中のローディング状態
    const [isGenerating, setIsGenerating] = useState(false);

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
                    alert(`エラーが発生しました: ${errorData.detail || '不明なエラー'}`);
                }
            }  
        } catch (error) {
            console.error("API 通信エラー", error);
            alert("ネットワークエラーが発生しました。");
        } finally {
            setIsGenerating(false);
        }
    };

    return {
        comment, setComment,
        university, setUniversity,
        isGenerating,
        handleGenerate
    };
}