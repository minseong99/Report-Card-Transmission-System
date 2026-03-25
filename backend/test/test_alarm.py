import os
import sys 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_trigger_draft_generation():
    # テスト用のダミーりクェスとデータ
    payload = {
        "class_id": 5,
        "exam_date": "2026-04-10"
    }

    # APIにPOSTりクェスとを送信
    response = client.post("/api/drafts/alam-and-start-generation", params=payload)

    # HTTP ステータスコードが200であることを確認
    assert response.status_code == 200

    # 中身確認
    data = response.json()
    assert data["status"] == "success"

    # アラームメッセージにテスト用のダミーデータが含まれているか確認
    assert f"クラスID:{payload['class_id']}" in data["message"]
    assert f"{payload['exam_date']}" in data["message"]

    print("\n APIエンドポイントのテスト成功")
    print("レスポンス内容:", data["message"])