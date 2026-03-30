import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './DraftPreview.css'; 

export default function DraftPreview({ studentData, onClose }) {
    const draftData = studentData;
    const studentSubjects = useMemo(() => {
        if (!draftData || !draftData.currentScores) return [];
        return draftData.currentScores.map(s => s.subject);
    }, [draftData]);

    // 科目別の固有Color
    const colorPalette = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"];
    
    const subjectColors = useMemo(() => {
        const colors = {};
        studentSubjects.forEach((sub, index) => {
            colors[sub] = colorPalette[index % colorPalette.length];
        });
        return colors;
    }, [studentSubjects]);
    
    // button toggle state
    const [activeLines, setActiveLines] = useState({});
    useEffect(() => {
        const initialActive = {};
        studentSubjects.forEach(sub => {
            initialActive[sub] = true;
        });
        setActiveLines(initialActive);
    }, [studentSubjects]);


    // グラフにある科目の情報toggleボタン
    const toggleSubject = (subject) => {
        setActiveLines(prev => ({
            ...prev,
            [subject]: !prev[subject]
        }));
    };


    // コメントState
    const [comment, setComment] = useState("\n各科目でバランスよく得点できています。特に英語の伸びが顕著です。次回の模試に向けて数学の応用問題に注力しましょう。");
    const [university, setUniversity] = useState("東京大学 理科一類 (B判定)\n早稲田大学 基幹理工学部 (A判定)");
    const [isGenerating, setIsGenerating] = useState(false);

    // 成績表生成ボタン
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
                    student_id: draftData.studentId,
                    exam_date:examDate,
                    comment: comment,
                    university: university
                })
            });
            if (response.ok) {
                const result = await response.json();
                alert(`${result.message}\n URL : ${result.file_url}`);
                onClose();
            }else {
                const errorData = await response.json()
            }
        } catch (error) {
            console.error("API 通信エラー", error);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="draft-modal-overlay">
            <div className="draft-modal-content">
                <div className="draft-header">
                    <h2>成績表プレビュー (確認・編集)</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="draft-body">
                    {/* top: 学生予約情報 */}
                    <div className="summary-cards">
                        <div className="card student-info">
                            <h3>生徒情報</h3>
                            <p className="name">{draftData.studentName}</p>
                            <p className="id">ID: {draftData.class_id}組</p>
                        </div>
                        <div className="card rank-info">
                            <h3>総合評価</h3>
                            <div className="ranks">
                                <div><span className="label">全校順位</span><span className="value">{draftData.overallRank}位</span></div>
                                <div><span className="label">クラス順位</span><span className="value">{draftData.classRank}位</span></div>
                            </div>
                        </div>
                    </div>

                    <div className="details-layout">
                        {/* 左: 成績詳細表 & グラフ */}
                        <div className="left-column">
                            <div className="section">
                                <h3>今回の成績詳細</h3>
                                <table className="score-table">
                                    <thead>
                                        <tr>
                                            <th>科目</th><th>点数</th><th>偏差値</th><th>全校順位</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {draftData.currentScores.map((s, idx) => (
                                            <tr key={idx}>
                                                <td>{s.subject}</td>
                                                <td className="highlight">{s.score}</td>
                                                <td >{s.hensachi.toFixed(1)}</td>
                                                <td>{s.overall_rank}位</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="section">
                                <h3>全科目の得点推移</h3>
                                <div className="chart-filters">
                                    <span className="filter-label">表示切替:</span>
                                    {Object.entries(subjectColors).map(([subject, color]) => (
                                        <button
                                            key={subject}
                                            className={`filter-btn ${activeLines[subject] ? 'active' : ''}`}
                                            style={{ 
                                                backgroundColor: activeLines[subject] ? color : '#f1f5f9',
                                                color: activeLines[subject] ? 'white' : '#64748b',
                                                borderColor: activeLines[subject] ? color : '#e2e8f0'
                                            }}
                                            onClick={() => toggleSubject(subject)}
                                        >
                                            {subject}
                                        </button>
                                    ))}
                                </div>
                                <div className="chart-container">
                                    <ResponsiveContainer width="100%" height={250}>
                                        <LineChart data={draftData.trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                            <XAxis dataKey="month" tick={{fontSize: 12}} />
                                            <YAxis domain={[0, 100]} tick={{fontSize: 12}} />
                                            <Tooltip />
                                            <Legend wrapperStyle={{fontSize: "12px"}}/>
                                            
                                            {Object.entries(subjectColors).map(([subject, color]) => (
                                                activeLines[subject] && (
                                                    <Line 
                                                        key={subject} 
                                                        type="monotone" 
                                                        dataKey={subject} 
                                                        stroke={color} 
                                                        strokeWidth={3} 
                                                        activeDot={{ r: 6 }} 
                                                    />
                                                )
                                            ))}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>

                        {/* 右: コメント & 推薦大学 */}
                        <div className="right-column">
                            <div className="section edit-section">
                                <h3>推薦大学 (編集可)</h3>
                                <p className="help-text">※システムが生成した草案です。必要に応じて修正してください。</p>
                                <textarea 
                                    value={university}
                                    onChange={(e) => setUniversity(e.target.value)}
                                    rows={3}
                                />
                            </div>

                            <div className="section edit-section">
                                <h3>講師コメント (編集可)</h3>
                                <p className="help-text">※生徒の成績推移に基づく分析結果です。</p>
                                <textarea 
                                    value={comment}
                                    onChange={(e) => setComment(e.target.value)}
                                    rows={6}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom: アクションボタン */}
                <div className="draft-footer">
                    <button className="btn-cancel" onClick={onClose}>キャンセル</button>
                    <button 
                        className="btn-submit" 
                        onClick={handleGenerate}
                        disabled={isGenerating}
                    >
                        {isGenerating ? '最終生成中...' : 'この内容で最終成績表を生成する'}
                    </button>
                </div>
            </div>
        </div>
    );
}

