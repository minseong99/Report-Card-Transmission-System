import React from 'react';

/**
 * 生徒の成績一覧を表示するテーブルコンポーネント
 * propsとして表示用データ(list)やタブの状態を受け取り、UIの描画のみに専念します。
 */
export default function StudentTable({ list, activeTab, startIndex, onPreviewClick }) {
    if (list.length === 0) {
        return (
            <div style={{ padding: '40px 20px', textAlign: 'center', color: '#94a3b8', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
                {activeTab === 'pending' ? '未処理の生徒はいません。' : '完了した生徒はまだいません。'}
            </div>
        );
    }

    return (
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', opacity: activeTab === 'completed' ? 0.8 : 1 }}>
            <thead style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                <tr>
                    <th style={{ padding: '12px', width: '50px' }}>No.</th>
                    <th style={{ padding: '12px' }}>生徒名</th>
                    <th style={{ padding: '12px' }}>総点</th>
                    <th style={{ padding: '12px' }}>クラス順位</th>
                    <th style={{ padding: '12px' }}>全校順位</th>
                    <th style={{ padding: '12px', textAlign: 'center' }}>
                        {activeTab === 'pending' ? 'アクション' : '成績表'}
                    </th>
                </tr>
            </thead>
            <tbody>
                {list.map((student, index) => (
                    <tr key={student.studentId} style={{ borderBottom: '1px solid #f1f5f9', backgroundColor: activeTab === 'completed' ? '#f8fafc' : 'white' }}>
                        <td style={{ padding: '12px', color: '#94a3b8', fontWeight: 'bold' }}>{startIndex + index + 1}</td>
                        <td style={{ padding: '12px', fontWeight: 'bold', color: activeTab === 'completed' ? '#64748b' : '#333' }}>{student.studentName}</td>
                        <td style={{ padding: '12px', color: activeTab === 'completed' ? '#64748b' : '#333' }}>{student.totalScore}点</td>
                        <td style={{ padding: '12px', color: activeTab === 'pending' ? '#64748b' : '#333' }}>{student.classRank}位</td>
                        <td style={{ padding: '12px', color: activeTab === 'completed' ? '#64748b' : '#333' }}>{student.overallRank}位</td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                            {activeTab === 'pending' ? (
                                <button 
                                    style={{ padding: '6px 12px', backgroundColor: '#3ea1b9', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                                    onClick={() => onPreviewClick(student)}
                                >
                                    プレビュー
                                </button>
                            ) : (
                                <a
                                    href={student.fileUrl} 
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: '#3b82f6', textDecoration: 'underline', cursor: 'pointer', fontWeight: 'bold' }}
                                >
                                    成績表を見る
                                </a>
                            )}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}