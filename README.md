#  学習塾向け 成績表自動生成・一括送信システム
(Report Card Auto-Generation & Bulk Send System for Tutoring Academy)

本システムは講師の業務改善のため、講師の「保護者への成績表送信プロセス業務改善」を目的としています。
採点完了から成績表（PDF）の生成、保護者への送信までの一連の業務フローを自動化し、講師の業務負担を大幅に削減します。

## 主な機能 

* **ダッシュボード (Dashboard)**
  * カスタムフック (`useDashboardData`) を用いたビジネスロジックの分離。
  * ポーリング(Polling)通信による、バックエンドとの安定したリアルタイム状態同期。
  * 未確認の採点データが存在する場合、スマートモーダルで自動生成をリマインド。
* **大規模データの一括バックグラウンド処理 (Bulk Background Processing)**
  * 1,000名規模の全校生徒データの偏差値・順位（クラス順位・全校順位・各科目順位）の自動計算。
  * FastAPIの `BackgroundTasks` を活用し、重いPDF生成処理や一括送信処理を非同期で実行。UIのブロック(フリーズ)を防止。
* **成績プレビュー＆リアルタイム再計算**
  * 送信前に個別の成績表をプレビューし、点数を直接修正可能。
  * 修正時は、影響を受ける全生徒の順位・偏差値をシステムが即座に再計算。

## 技術スタック (Tech Stack)

### Frontend
* **React / React Router**: SPAによる高速な画面遷移
* **Custom Hooks**: 複雑な状態管理とAPI通信の隠蔽化
* **CSS**: レスポンシブで直感的なUIデザイン

### Backend
* **Python / FastAPI**: 高速なAPIサーバーと非同期処理ルーティング
* **SQLAlchemy**: ORMを用いた効率的なデータベース操作

### Infrastructure 
* **Docker / Docker Compose**: フロントエンド・バックエンド・DB・MinIOのコンテナ化による一貫した開発・実行環境の構築

## システムアの特徴

1. **イベント駆動型アクション**: 講師が「一括生成」をリクエストすると、FastAPIが即座に `200 OK` を返し、実際の重い処理はバックグラウンドワーカースレッドへ委譲。
2. **安定性の高い状態同期**:5秒間隔の安全なポーリング方式を採用。ネットワークの切断や再ログイン時でも、一貫した最新のDB状態を復元可能。
3. **安全なローカルストレージ活用**: ユーザーが一度閉じたスマートモーダルを永続的に記憶させ、不必要なポップアップによるUX低下を防止。

## 起動方法 (Getting Started)

Docker Composeを利用して、アプリケーション全体をワンコマンドで起動できます。

```bash
# リポジトリのクローン
$git clone [https://github.com/your-username/your-repo-name.git$](https://github.com/your-username/your-repo-name.git$) cd your-repo-name

# Dockerコンテナのビルドと起動
$ docker-compose up -d --build

# 起動確認
# Frontend: http://localhost:5173

# dummy data
docker-compose exec backend python generate-dummy/seed.py     # 学生、講師、保護者のダミーデータ準備
# 過去の試験成績ダミーデータ
docker-compose exec backend python generate-dummy/insert_past_score_data.py　1
docker-compose exec backend python generate-dummy/insert_past_score_data.py　2

# test : １０００名分の成績入力
docker-compose exec backend pytest -s ./test/test_alarm.py -k "test_api_1000_students_bulk_process"
　　
