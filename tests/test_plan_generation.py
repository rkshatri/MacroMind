from environment.day_env import DayEnv
from agent.ppo_agent import run_episode_with_plan


class TrackingEnv(DayEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_calls = 0

    def reset(self, *, seed=None, options=None):
        self.reset_calls += 1
        return super().reset(seed=seed, options=options)


class DummyModel:
    def predict(self, obs, deterministic=True):
        return 2, None


def test_run_episode_with_plan_preserves_preconfigured_schedule():
    env = TrackingEnv(wake_hour=6, wake_minute=0)
    env.reset()

    env.generated_busy_blocks = [4, 5]
    env.busy_blocks = [4, 5]
    env.workout_steps = []
    env.current_archetype = "custom"

    plan = run_episode_with_plan(DummyModel(), env, reset=False)

    assert env.reset_calls == 1
    assert plan["schedule_type"] == "custom"
    assert plan["busy_blocks"] == [env.step_to_time(4), env.step_to_time(5)]
