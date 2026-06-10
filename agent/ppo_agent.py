from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from environment.day_env import DayEnv


def make_env():
    """
    Create and return a fresh environment wrapped in Monitor for automatic logging.
    
    Returns:
        Monitor: A monitored DayEnv instance that logs episode rewards automatically.
    """
    env = DayEnv()
    env = Monitor(env)
    return env

class MacroMindAgent:
    """
    PPO agent for macro tracking environment using stable-baselines3.
    """

    def __init__(self, env, model_path=None):
        """
        Initialize the PPO agent.
        
        Args:
            env: The DayEnv environment (preferably wrapped in Monitor).
            model_path (str, optional): Path to a saved PPO model to load.
                If None, creates a fresh model with default hyperparameters.
        """
        self.env = env
        
        if model_path:
            self.model = PPO.load(model_path)
        else:
            self.model = PPO(
                policy="MlpPolicy",
                env=env,
                learning_rate=3e-4,
                n_steps=300,  # 30 steps × 10 episodes per update
                batch_size=60,
                n_epochs=10,
                gamma=0.99,
                clip_range=0.2,
                verbose=1
            )

    def train(self, total_timesteps, save_path):
        """
        Train the agent for a given number of timesteps and save the model.
        
        Args:
            total_timesteps (int): Total number of timesteps to train for.
            save_path (str): Path where the trained model will be saved.
        """
        self.model.learn(total_timesteps=total_timesteps)
        self.model.save(save_path)
        print(f"Model saved at {save_path}")

    def predict(self, obs):
        """
        Get the deterministic action for a given observation.
        
        Args:
            obs (np.ndarray): The observation (13-value state vector).
            
        Returns:
            int: The predicted action (0=wait, 1=snack, 2=meal).
        """
        action, _ = self.model.predict(obs, deterministic=True)
        return action

    def evaluate(self, n_episodes=10, verbose=False):
        """
        Evaluate the agent over n_episodes without training.
        
        Runs full episodes and tracks cumulative rewards. Prints mean and std of rewards.
        If verbose=True, prints step-by-step details for the first episode.
        
        Args:
            n_episodes (int): Number of episodes to evaluate. Default: 10.
            verbose (bool): If True, prints detailed step-by-step info for first episode. Default: False.
        """
        import numpy as np
        
        def step_time_label(step_index):
            total_minutes = 8 * 60 + step_index * 30
            hour = (total_minutes // 60) % 12
            if hour == 0:
                hour = 12
            minute = total_minutes % 60
            suffix = "am" if total_minutes < 12 * 60 else "pm"
            return f"{hour}:{minute:02d}{suffix}"
        
        episode_rewards = []
        
        for episode in range(n_episodes):
            obs, _ = self.env.reset()
            total_reward = 0.0
            done = False
            step = 0
            
            if verbose and episode == 0:
                print(f"Schedule: {self.env.env.current_archetype}")
                print(f"Busy steps: {self.env.env.busy_blocks}")
                print(f"Workout steps: {self.env.env.workout_steps}")
                print("time     | schedule | action | food                      | hunger | calories | protein | carbs | fat | reward")
            
            while not done:
                action = self.predict(obs)
                obs, reward, done, truncated, info = self.env.step(action)
                total_reward += reward

                effective_action = info.get("effective_action", action)
                food_name = (self.env.env.last_food_eaten or "---")
                if effective_action == 0:
                    action_text = "---"
                    food_name = "---"
                elif effective_action == 1:
                    action_text = "snack"
                elif effective_action == 2:
                    action_text = "meal"
                else:
                    action_text = "unknown"

                is_busy = info.get("is_busy")
                is_workout = info.get("is_workout")
                if is_busy == True:
                    schedule = "busy"
                elif is_workout == True:
                    schedule = "workout"
                else:
                    schedule = "---"
                
                if verbose and episode == 0:
                    print(
                        f"{step_time_label(step):8s} | "
                        f"{schedule:8s} | "
                        f"{action_text:6s} | "
                        f"{food_name:25.40s} | "
                        f"{self.env.env.hunger:6.3f} | "
                        f"{self.env.env.calories_consumed:8.0f} | "
                        f"{self.env.env.protein_consumed:7.0f} | "
                        f"{self.env.env.carbs_consumed:5.0f} | "
                        f"{self.env.env.fat_consumed:3.0f} | "
                        f"{reward:6.3f}"
                    )
                
                step += 1
            
            episode_rewards.append(total_reward)
        
        mean_reward = np.mean(episode_rewards)
        std_reward = np.std(episode_rewards)
        
        print(f"Evaluation over {n_episodes} episodes:")
        print(f"  Mean reward: {mean_reward:.3f}")
        print(f"  Std reward: {std_reward:.3f}")

def run_episode_with_plan(model, env):
    obs, _ = env.reset()
    done = False
    meals = []

    prev_calories = 0
    prev_protein = 0
    prev_carbs = 0
    prev_fat = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)

        is_cooldown = env.fullness_cooldown > 0
        is_busy = (env.current_step + 1) in env.busy_blocks
        is_workout = (env.current_step + 1) in env.workout_steps
        effective = 0 if (is_cooldown or is_busy or is_workout) else int(action)

        obs, reward, done, truncated, info = env.step(action)

        if effective in [1, 2] and env.last_food_eaten:
            time_label = step_to_time(env.current_step)
            meals.append({
                "time": time_label,
                "type": "snack" if effective == 1 else "meal",
                "food": env.last_food_eaten,
                "calories": env.calories_consumed - prev_calories,
                "protein": env.protein_consumed - prev_protein,
                "carbs": env.carbs_consumed - prev_carbs,
                "fat": env.fat_consumed - prev_fat
            })
            prev_calories = env.calories_consumed
            prev_protein = env.protein_consumed
            prev_carbs = env.carbs_consumed
            prev_fat = env.fat_consumed

    meal_plan = {
        "schedule_type": env.current_archetype,
        "busy_steps": env.busy_blocks,
        "workout_steps": env.workout_steps,
        "meals": meals,
        "totals": {
            "calories": env.calories_consumed,
            "protein": env.protein_consumed,
            "carbs": env.carbs_consumed,
            "fat": env.fat_consumed
        },
        "targets": {
            "calories": env.target_calories,
            "protein": env.target_protein,
            "carbs": env.target_carbs,
            "fat": env.target_fat
        }
    }

    return meal_plan
    

def step_to_time(step):
    minutes = 6 * 60 + step * 30
    hours = minutes // 60
    mins = minutes % 60
    ampm = "am" if hours < 12 else "pm"
    hours = hours if hours <= 12 else hours - 12
    return f"{hours}:{mins:02d}{ampm}"


# Test
if __name__ == "__main__":

    env = make_env()
    agent = MacroMindAgent(env=env, model_path='models/ppo_macromind.zip')
    print(run_episode_with_plan(model=agent, env=env))
