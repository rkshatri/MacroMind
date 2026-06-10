import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from stable_baselines3 import PPO
from environment.day_env import DayEnv
from agent.ppo_agent import run_episode_with_plan
from rag.explainer import explain_meal_plan
from rag.embedder import load_vector_store

env = DayEnv()
model = PPO.load("models/ppo_macromind", env=env)
vector_store = load_vector_store("rag/vector_store")

meal_plan = run_episode_with_plan(model, env)
explanation = explain_meal_plan(meal_plan, vector_store)

print(explanation)