import threading
import uuid

class TaskStore:
    def __init__(self):
        self._tasks = {}
        self._lock = threading.Lock()

    def create(self, kind):
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "kind": kind,
                "status": "pending",
                "progress": 0,
                "message": "",
                "result": None,
                "error": None,
            }
        return task_id

    def update(self, task_id, progress=None, status=None, message=None, result=None, error=None):
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            if progress is not None:
                t["progress"] = progress
            if status is not None:
                t["status"] = status
            if message is not None:
                t["message"] = message
            if result is not None:
                t["result"] = result
            if error is not None:
                t["error"] = error

    def get(self, task_id):
        with self._lock:
            return self._tasks.get(task_id)

    def complete(self, task_id, result=None):
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            t["status"] = "completed"
            t["progress"] = 100
            t["result"] = result

task_store = TaskStore()