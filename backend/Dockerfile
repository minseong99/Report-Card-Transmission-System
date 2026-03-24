# ベースイメージ
FROM python:3.11-slim

# コンテナ内の作業Directory
WORKDIR /app

# ホストのrequirements.txtをコンテナにコピー
COPY requirements.txt .

# パッケージのインストール
RUN pip install --no-cache-dir -r requirements.txt 

# アプリケーションのソースコードを全てコピー
COPY . .

# コンテナが外部と通信するポート
EXPOSE 8000

# コンテナ起動時に実行されるコメンど
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
