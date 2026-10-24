# ai-component-workshop

AI-powered UI generator. Transforms raw text prompts or Figma nodes into production-ready Vue 3 + Tailwind components using a multi-agent LLM pipeline.

## 🚀 Features
* **Multi-Agent Pipeline:** Refiner -> Architect -> Vue Coder.
* **Figma Integration:** Fetch node structures directly by ID or SVG reference.
* **Local & Private:** Runs entirely on your hardware via Ollama.
* **Live SSE Streaming:** Real-time generation progress in the UI.

---

## 🛠️ Requirements
* **Python:** 3.10+ (рекомендуется 3.11+ для встроенного `tomllib`).
* **Ollama:** Установленный и запущенный [Ollama](https://ollama.com/) с моделями.
* **Node.js / Vite (Опционально):** Если планируете дорабатывать фронтенд (в текущей версии фронтенд на чистом HTML/JS).

---

## 📦 Installation

### 1. **Клонируйте репозиторий:**

```bash
git clone https://github.com/your-username/ai-component-workshop.git
cd ai-component-workshop
```

### 2. **Создайте и активируйте виртуальное окружение:**

```bash
python -m venv .venv
source .venv/bin/activate  # Для Linux/Mac/WSL
# или .venv\Scripts\activate для Windows
```

### 3. **Установите зависимости:**

```bash
pip install -r requirements.txt
```

---

## 🖥️ System Requirements

Для комфортной работы проекта (запуск двух локальных LLM) ваш компьютер должен обладать достаточным объемом оперативной памяти и VRAM.

### Minimum (Запустится, но будет медленно)
* **OS:** Windows 10/11 (с WSL2), Linux или macOS.
* **RAM:** 16 GB (система + одна модель).
* **VRAM (GPU):** 8 GB (для квантованных моделей).
* **Disk:** ~20 GB свободного места (Ollama + модели).

### Recommended (Для комфортной разработки)
* **RAM:** 32 GB+.
* **VRAM (GPU):** 12–16 GB (например, RTX 3060 12GB, RTX 4070).
* **Disk:** SSD NVMe для быстрой загрузки моделей.

---

## 🧠 Recommended Models

Проект использует **две модели**: 
1. **Архитектор** (в `.env` указывается первой) — пишет ТЗ (Агент 0) и проектирует структуру Figma (Агент 1).
2. **Кодер** (вторая модель) — переводит структуру в Vue 3 + TypeScript (Агент 2).

Указать их можно в `.env` через запятую: `MODELS=модель_архитектора,модель_кодера`

### Вариант 1: Баланс (Рекомендуемый)
* **Архитектор:** `deepseek-r1:14b` (Q4_K_M ~8 GB) — отлично следует инструкциям и генерирует сложные JSON.
* **Кодер:** `mistral-nemo:12b` (Q4_K_M ~8 GB) — хорошо знает Vue 3 и TypeScript.

### Вариант 2: Легкий (Для слабых ПК / 8 GB VRAM)
* **Архитектор:** `deepseek-r1:7b` (~5 GB) или `qwen2.5-coder:7b`
* **Кодер:** `qwen2.5-coder:7b` (~5 GB)

### Вариант 3: Качество (Для мощных ПК / 16+ GB VRAM)
* **Архитектор:** `deepseek-r1:14b` (Q5 или Q8)
* **Кодер:** `mistral-nemo:12b` (Q5 или Q8)

---

## ⚙️ Configuration

Перед запуском необходимо настроить два файла.

### 1. `.env` (Секреты и модели)
Скопируйте `.env.example` в `.env` и заполните:

```ini
FIGMA_TOKEN=your_figma_personal_access_token
FIGMA_FILE_KEY=your_file_key
FIGMA_BASE_URL=https://api.figma.com/v1/files/

OLLAMA_API_URL=http://localhost:11434/api/chat
# Первая модель - Архитектор (ТЗ + Figma). Вторая модель - Кодер (Vue).
MODELS=deepseek-r1:14b,mistral-nemo:12b
```

### 2. `config.toml` (Параметры ИИ)
Здесь настраиваются `temperature`, `num_predict`, `keep_alive` для каждого агента:

```toml
[ollama.global]
stream = false
format = "json"
default_keep_alive = 0

[ollama.agents.refiner]
# Использует MODELS[0] (Архитектор)
keep_alive = 0
temperature = 0.1
num_predict = 1024
num_ctx = 8192

[ollama.agents.architect]
# Использует MODELS[0] (Архитектор)
keep_alive = "5m"
temperature = 0.2
num_predict = 2048
num_ctx = 8192

[ollama.agents.vue]
# Использует MODELS[1] (Кодер)
keep_alive = "5m"
temperature = 0.1
num_predict = 4096
num_ctx = 8192
```

---

## 🏃‍♂️ Running the App

Запустите сервер через единую точку входа:

```bash
python run.py
```

После успешного старта откройте в браузере:
👉 **http://localhost:5555/**

---

## 🧪 Running Tests

Для проверки конфигурации и логгера:

```bash
pytest
```

---

## 📂 Project Structure

```text
├── app/
│   ├── agents/          # ИИ-агенты (refiner, figma, vue)
│   ├── llm/             # Промпты, статусы, примеры (JSON)
│   ├── utils/           # Логгер, очистка JSON
│   ├── config.py        # Загрузка .env + TOML
│   └── routes.py        # Flask эндпоинты и SSE
├── .env.example
├── config.toml
├── run.py               # Точка входа
└── requirements.txt
```

---

## 📝 License
MIT