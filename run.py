# run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("🚀 Многоагентный сервер-мост успешно запущен.", flush=True)
    print("🔗 Веб-интерфейс: http://localhost:5555/", flush=True)
    app.run(host="0.0.0.0", port=5555, debug=False)