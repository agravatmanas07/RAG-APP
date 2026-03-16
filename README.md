# 🧠 DataMind — Production RAG Application
**By Manas Agravat | AI & Data Engineer**

A full-stack Retrieval-Augmented Generation (RAG) app that lets you upload CSV/Excel files and ask natural language questions about your data.

---

## 🏗️ Architecture

```
┌─────────────────┐     HTTP      ┌──────────────────────┐
│   Frontend      │ ──────────── ▶│   FastAPI Backend    │
│   (HTML/JS)     │               │                      │
│   Port 3000     │               │  ┌────────────────┐  │
└─────────────────┘               │  │   ChromaDB     │  │
                                  │  │  (Embeddings)  │  │
                                  │  └────────────────┘  │
                                  │  ┌────────────────┐  │
                                  │  │  Claude AI API │  │
                                  │  │  (Answers)     │  │
                                  │  └────────────────┘  │
                                  └──────────────────────┘
```

## 🚀 Quick Start

### Option 1 — Docker (Recommended)
```bash
# 1. Clone & enter project
cd rag-app

# 2. Set your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 3. Run everything
docker-compose up --build

# App: http://localhost:3000
# API: http://localhost:8000/docs
```

### Option 2 — Manual
```bash
# Backend
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/stores` | List all data stores |
| POST | `/upload` | Upload CSV/Excel file |
| POST | `/query` | Ask a question |
| DELETE | `/stores/{id}` | Delete a store |

### Example Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"store_id": "abc12345", "question": "What is the total revenue?", "top_k": 5}'
```

---

## 🗂️ Project Structure
```
rag-app/
├── backend/
│   ├── main.py           # FastAPI app + RAG logic
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile
├── frontend/
│   └── index.html        # Full UI (single file)
├── data/
│   └── sample_orders.csv # Test data
├── docker-compose.yml
└── README.md
```

---

## 🧠 How RAG Works Here

1. **Upload** — CSV/Excel rows are converted to text chunks
2. **Embed** — ChromaDB embeds each chunk using sentence transformers
3. **Query** — User question is embedded & top-K similar chunks retrieved
4. **Generate** — Claude AI generates answer using retrieved context
5. **Return** — Answer + source chunks sent back to UI

---

## 🛠️ Tech Stack
- **Backend**: Python 3.11, FastAPI, ChromaDB, Pandas
- **AI**: Anthropic Claude (claude-sonnet-4-20250514)
- **Frontend**: Vanilla HTML/CSS/JS (zero dependencies)
- **Infra**: Docker + Nginx

---

## 👤 Author
**Manas Agravat** — AI & Data Engineer  
📧 manasagravat5@gmail.com | 📞 +33 7 45 91 86 94
