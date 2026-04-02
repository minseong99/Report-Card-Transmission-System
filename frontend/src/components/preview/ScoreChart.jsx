import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * 成績推移を可視化する折れ線グラフコンポーネント
 * 科目別の表示切り替えロジックもこの中にカプセル化（隠蔽）します。
 */
export default function ScoreChart({ trendData, currentScores }) {
    // 科目リストの抽出
    const studentSubjects = useMemo(() => {
        if (!currentScores) return [];
        return currentScores.map(s => s.subject);
    }, [currentScores]);

    // 科目別の固有カラー設定
    const colorPalette = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"];
    const subjectColors = useMemo(() => {
        const colors = {};
        studentSubjects.forEach((sub, index) => {
            colors[sub] = colorPalette[index % colorPalette.length];
        });
        return colors;
    }, [studentSubjects]);
    
    // グラフの表示/非表示トグル状態
    const [activeLines, setActiveLines] = useState({});
    
    useEffect(() => {
        const initialActive = {};
        studentSubjects.forEach(sub => initialActive[sub] = true);
        setActiveLines(initialActive);
    }, [studentSubjects]);

    const toggleSubject = (subject) => {
        setActiveLines(prev => ({ ...prev, [subject]: !prev[subject] }));
    };

    return (
        <div className="section">
            <h3>全科目の得点推移</h3>
            
            {/* 科目フィルタリングボタン */}
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

            {/* Recharts グラフ描画エリア */}
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="month" tick={{fontSize: 12}} />
                        <YAxis domain={[0, 100]} tick={{fontSize: 12}} />
                        <Tooltip />
                        <Legend wrapperStyle={{fontSize: "12px"}}/>
                        
                        {Object.entries(subjectColors).map(([subject, color]) => (
                            activeLines[subject] && (
                                <Line 
                                    key={subject} type="monotone" dataKey={subject} 
                                    stroke={color} strokeWidth={1} activeDot={{ r: 6 }} 
                                />
                            )
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}