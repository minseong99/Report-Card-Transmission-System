import asyncio
from typing import Dict, List 

class EventManager:
    """
    SSE(Server-Sent Events)のための接続管理とメッセージ配信(Broadcast)を行うクラスです。
    """
    def __init__(self):
        # class_idをキーにして、接続されている各クライアントのQueue(非同期キュー)リストを保存します。
        self.connections: Dict[int, List[asyncio.Queue]] = {}
        self.main_loop = None # メインループ(Uvicorn)を記憶する変数
    
    async def subscribe(self, class_id: int) -> asyncio.Queue:
        """クライアントがSSEエンドポイントに接続した際に専用のQueueを作成して登録します。"""

        # 最初のクライアントが接続した際、Uvicornのメインループを保存します
        if self.main_loop is None:
            self.main_loop = asyncio.get_running_loop()

        queue = asyncio.Queue()
        if class_id not in self.connections:
            self.connections[class_id] = []
        self.connections[class_id].append(queue)
        return queue
    
    def unsubscribe(self, class_id: int, queue: asyncio.Queue):
        """"クライアントが切れた際にQueueを削除し、メモリリークを防ぎます。"""
        if class_id in self.connections and queue in self.connections[class_id]:
            self.connections[class_id].remove(queue)
            # 誰もいなくなったらキーを削除
            if not self.connections[class_id]:
                del self.connections[class_id]

    async def broadcast(self, class_id: int, message: str):
        """特定のクラスに接続している全クライアントに非同期でメッセージを送信します。"""
        if class_id in self.connections:
            for queue in self.connections[class_id]:
                await queue.put(message)
    
    def sync_broadcast(self, class_id: int, message: str):
        """
        同期(sync)関数から安全に非同期(Async)のbroadcastを呼び出すためのブリッジ関数
        バックグラウンドタスクなどの通常のdef関数の中から呼び出す際に使用します。
        """
        """
        別スレッド(def関数やBackgroundTask)から、
        安全にメインスレッドのループへ処理を渡す(Thread-safe)ブリッジ関数です。
        """
        if self.main_loop and self.main_loop.is_running():
            # 異なるスレッドからメインループへタスクを安全に投げ込みます！
            asyncio.run_coroutine_threadsafe(self.broadcast(class_id, message), self.main_loop)
        else:
            print("警告: 実行中のメインループが見つかりません。")

# アプリ全体で共有するシングルトン・インスタンスを作成します。
event_manager = EventManager()