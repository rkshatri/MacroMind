import random
from environment.day_env import DayEnv

def test_environment_step_loop():
    env = DayEnv()
    obs, info = env.reset()

    print("Starting environment loop")
    print(
        "step | action | overridden | hunger | fullness | cooldown | calories_rem | protein_rem | carbs_rem | fat_rem | reward"
    )

    for step in range(env.total_steps):
        action = env.action_space.sample()
        next_step = env.current_step + 1
        overridden = next_step in env.busy_blocks or env.fullness_cooldown > 0

        obs, reward, done, truncated, info = env.step(action)

        match action:
            case 0:
                action_text = "wait"
            case 1:
                action_text = "snack"
            case 2:
                action_text = "meal"
            case _:
                action_text = "unknown"

        print(
            f"{step + 1:4d} | "
            f"{action_text:5s} | "
            f"{str(overridden):9s} | "
            f"{env.hunger:6.3f} | "
            f"{env.fullness:8.3f} | "
            f"{env.fullness_cooldown:8d} | "
            f"{env.calories_remaining:12.1f} | "
            f"{env.protein_remaining:11.1f} | "
            f"{env.carbs_remaining:9.1f} | "
            f"{env.fat_remaining:7.1f} | "
            f"{reward:6.3f}"
        )

        if done:
            break

    assert env.current_step == env.total_steps

test_environment_step_loop()