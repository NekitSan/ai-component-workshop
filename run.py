import os

from dotenv import load_dotenv

from app.utils import find_free_port

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    is_dev = os.getenv("APP_ENV", "prod").lower() == "dev"
    port = int(os.getenv("APP_PORT", find_free_port()))
    mode = "DEV 🛠️ " if is_dev else "PROD 🚀 "
    
    print(f"🌐 Запуск сервера ( Режим: {mode} )")
    print(f"🔗 Ссылка: http://127.0.0.1:{port}")
    
    os.environ["APP_PORT"] = str(port)
    
    app.run(
        host="127.0.0.1", 
        port=port, 
        debug=is_dev, 
        use_reloader=is_dev
    )