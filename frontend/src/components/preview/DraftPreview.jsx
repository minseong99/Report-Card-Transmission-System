import React from 'react';
import './DraftPreview.css'; 
import { useDraftPreview } from '../../hooks/useDraftPreview';
import ScoreChart from './ScoreChart';

/**
 * 成績表の最終確認と編集を行うモーダルコンポーネント
 * 複雑なロジックやグラフ描画は外部のフックとサブコンポーネントに委譲しています。
 */
export default function DraftPreview({ studentData, examDate, onClose, onSuccess }) {
    const draftData = studentData;

    // カスタムフックから状態と通信ロジックを取得
    const { 
        comment, setComment, 
        university, setUniversity, 
        isGenerating, handleGenerate 
    } = useDraftPreview(studentData, examDate, onSuccess);

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
                                                <td>{s.hensachi.toFixed(1)}</td>
                                                <td>{s.overall_rank}位</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
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

