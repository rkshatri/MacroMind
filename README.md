# MacroMind

A reinforcement learning agent that learns to optimize daily nutrition 
around your schedule and physical activity.

## What it does
MacroMind simulates a full day in 30-minute timesteps. A PPO agent learns 
when to eat, what to eat, and how much by balancing hunger, macro targets, 
and a dynamic daily schedule. The RAG pipeline is built using LangChain and explains 
the agent's meal plan in plain language with citations from nutrition research.

## Stack
- **RL:** Stable-Baselines3 (PPO), Gymnasium
- **Data:** USDA FoodData Central API
- **LLM Layer:** Ollama, LangChain, FAISS
- **Viz:** FastAPI, React

## Getting Started

### Prerequisites
- Python 3.11
- Node.js 20.19+ or 22.12+ (required by Vite 8)
- *Optional:* [Ollama](https://ollama.com) for the natural-language meal plan explanations.
  Without it, the API still returns a plan with a short plain-text summary.

### 1. Clone
```sh
git clone https://github.com/rkshatri/MacroMind.git
cd MacroMind
```

### 2. Backend (FastAPI)
Run these from the repository root. You only need to create the virtual environment and train the model once.
```sh
python3.11 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
python -m pip install -r requirements.txt

# Train the PPO agent (writes models/ppo_macromind.zip, takes a few minutes)
python train.py

# Start the API at http://localhost:8000 (interactive docs at /docs)
python -m uvicorn api.main:app --reload --port 8000
```

> Use `python -m pip` / `python -m uvicorn` rather than bare `pip` / `uvicorn`.
> Venv scripts hard-code absolute paths, so they break if the project folder is moved
> or its path contains spaces. If you move the folder, delete `venv/` and recreate it.

### 3. Frontend (React + Vite)
In a second terminal:
```sh
cd frontend
npm ci
npm run dev
```
Open http://localhost:5173. The frontend calls the API at `http://localhost:8000/api`.

### Optional: LLM explanations
```sh
ollama pull llama3.2
ollama pull nomic-embed-text
ollama serve                        # if Ollama isn't already running
```

### Optional: USDA FoodData Central lookups
The food data the app uses (`data/foods/pantry.json`) is checked in, so no API key is needed to run it.
To query the USDA API with `data/build_food_library.py`, get a free key (see `.env.example`) and run:
```sh
export FDC_API_KEY=your_key_here
python data/build_food_library.py
```

### Tests
```sh
python -m pytest
```

## Project Status
Phase 5: Visualization

## Roadmap
- [x] Phase 1: RL Environment
- [x] Phase 2: PPO Agent
- [x] Phase 3: USDA Food Database
- [x] Phase 4: RAG + LangChain
- [x] Phase 5: Visualization
