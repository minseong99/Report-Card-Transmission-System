import React from 'react';
import './DraftPreview.css'; 
import { useDraftPreview } from '../../hooks/useDraftPreview';
import ScoreChart from './ScoreChart';

/**
 * 成績表の最終確認と編集を行うモーダルコンポーネント
 * 複雑なロジックやグラフ描画は外部のフックとサブコンポーネントに委譲しています。
 */
export default function DraftPreview({ studentData, examDate, onClose, onSuccess, onScoreUpdated }) {
    const draftData = studentData;

    // カスタムフックから状態と通信ロジックを取得
    const { 
        comment, setComment, 
        university, setUniversity, 
        isGenerating, handleGenerate,
        isEditMode, toggleEditMode, editScores, handleScoreChange, handleScoreUpdate, isUpdatingScore
    } = useDraftPreview(studentData, examDate, onSuccess, onScoreUpdated);

    return (
        <div className="draft-modal-overlay">
            <div className="draft-modal-content">
                
                {/* 1. ヘッダー領域 */}
                <div className="draft-header">
                    <h2>成績表プレビュー (確認・編集)</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="draft-body">
                    {/* 2. 生徒基本情報カード */}
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

                    {/* 3. メイン詳細レイアウト */}
                    <div className="details-layout">
                        {/* 左側: 成績テーブルとグラフ */}
                        <div className="left-column">
                            <div className="section">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                    <h3 style={{ margin: 0 }}>今回の成績詳細</h3>
                                    {!isEditMode ? (
                                        <button 
                                            onClick={toggleEditMode}
                                            style={{ backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', padding: '5px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px' }}
                                        >
                                            点数を修正
                                        </button>
                                    ) : null}
                                </div>

                                <table className="score-table">
                                    <thead>
                                        <tr>
                                            <th>科目</th>
                                            <th>点数</th>
                                            <th>偏差値</th>
                                            <th>全校順位</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {draftData.currentScores.map((s, idx) => (
                                            <tr key={idx} style={{ backgroundColor: isEditMode ? '#f8fafc' : 'transparent' }}>
                                                <td>{s.subject}</td>
                                                
                                                {/* 編集モード時のインプット UI */}
                                                <td>
                                                    {isEditMode ? (
                                                        <input 
                                                            type="number" 
                                                            min="0" max="100"
                                                            value={editScores[s.subject] !== undefined ? editScores[s.subject] : ''} 
                                                            onChange={(e) => handleScoreChange(s.subject, e.target.value)}
                                                            style={{ 
                                                                width: '60px', padding: '6px', borderRadius: '4px', 
                                                                border: '2px solid #3b82f6', outline: 'none', 
                                                                textAlign: 'center', fontWeight: 'bold', color: '#1e293b' 
                                                            }}
                                                        />
                                                    ) : (
                                                        <span className="highlight">{s.score}</span>
                                                    )}
                                                </td>
                                                
                                                {/* 編集モード中は変動予定のため薄く表示 */}
                                                <td style={{ color: isEditMode ? '#cbd5e1' : 'inherit' }}>{s.hensachi.toFixed(1)}</td>
                                                <td style={{ color: isEditMode ? '#cbd5e1' : 'inherit' }}>{s.overall_rank}位</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>

                                {/* 編集モード用の保存・キャンセルボタン */}
                                {isEditMode && (
                                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px', padding: '10px', backgroundColor: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
                                        <span style={{ fontSize: '12px', color: '#3b82f6', marginRight: 'auto', alignSelf: 'center' }}>保存すると順位と偏差値が自動再計算されます。</span>
                                        <button 
                                            onClick={toggleEditMode}
                                            style={{ padding: '6px 12px', backgroundColor: 'white', color: '#64748b', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}
                                        >
                                            キャンセル
                                        </button>
                                        <button 
                                            onClick={handleScoreUpdate}
                                            disabled={isUpdatingScore}
                                            style={{ padding: '6px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}
                                        >
                                            {isUpdatingScore ? '保存中...' : '一括保存する'}
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* 分離したグラフコンポーネントを配置 */}
                            <ScoreChart 
                                trendData={draftData.trendData} 
                                currentScores={draftData.currentScores} 
                            />
                        </div>

                        {/* 右側: 編集可能なテキストエリア */}
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

                {/* 4. フッター（アクションボタン） */}
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

