from agent.ppo_agent import make_env, MacroMindAgent

env = make_env()
agent = MacroMindAgent(env=env, model_path=None)

agent.train(total_timesteps=100000, save_path="./models/ppo_macromind")
agent.evaluate(verbose=True)