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

## Project Status
Phase 1 — Environment under construction

## Roadmap
- [x] Phase 1: RL Environment
- [x] Phase 2: PPO Agent
- [x] Phase 3: USDA Food Database
- [x] Phase 4: RAG + LangChain
- [x] Phase 5: Visualization
