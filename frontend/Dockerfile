# 軽量なNode.jsイメージを使用
FROM node:20-alpine

# 作業Directory設定
WORKDIR /app

# パッケージをコピーしてインストール
COPY package*.json ./
RUN npm install

# ソースコード全体コピー
COPY . .

# ViteのDefaultポート
EXPOSE 5173

# vite開発サーバを立ち上げる(--host: 外部アクセス許可)
CMD [ "npm", "run", "dev", "--", "--host" ]