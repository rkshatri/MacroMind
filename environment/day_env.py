import gymnasium
import numpy as np
import random
from gymnasium import spaces


class DayEnv(gymnasium.Env):
    """
    A Gym environment for simulating a day of macro tracking and food consumption.
    """
    
    def __init__(self):
        super().__init__()
        
        # Fixed macro targets (in grams or kcal)
        self.target_calories = 2000
        self.target_protein = 150
        self.target_carbs = 200
        self.target_fat = 65
        
        # Timestep constants
        self.total_steps = 48  # 30-minute intervals in a day
        self.snack_fullness_duration = 6  # steps
        self.meal_fullness_duration = 12  # steps
        
        # Observation space: 13 values between 0 and 1
        # (with macros remaining allowed to go negative)
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, -1]),
            high=np.array([1, 1, 1, 1,  2,  2,  2, 1, 1, 1, 1, 1,  2]),
            dtype=np.float32
        )
        
        # Action space: 3 discrete actions
        self.action_space = spaces.Discrete(3)
        
        # Placeholder instance variables for state
        self.hunger = None
        self.fullness = None
        self.current_step = None
        self.last_meal_step = None
        self.calories_consumed = None
        self.protein_consumed = None
        self.carbs_consumed = None
        self.fat_consumed = None
        self.calories_remaining = None
        self.protein_remaining = None
        self.carbs_remaining = None
        self.fat_remaining = None
        self.calories_burned = None
        self.meals_eaten = None
        self.snacks_eaten = None
        self.busy_blocks = None
        self.workout_steps = None
        self.fullness_cooldown = None

    def reset(self):
        """
        Reset the environment to the initial state.
        
        Returns:
            tuple: (observation, info)
        """
        # Three hardcoded schedule archetypes
        light_busy = [8, 9, 18, 19]
        light_workout = []  # No workouts on light days
        busy_busy = [8, 9, 10, 12, 13, 18, 19, 20, 22]
        busy_workout = []  # Busy days have busy times but no dedicated workouts
        workout_busy = [8, 9, 18, 19]  # Some busy times
        workout_workout = [6, 7, 12, 13]  # Dedicated workout times
        
        # Randomly pick an archetype
        archetype = random.choice(['light', 'busy', 'workout'])
        if archetype == 'light':
            self.busy_blocks = light_busy
            self.workout_steps = light_workout
        elif archetype == 'busy':
            self.busy_blocks = busy_busy
            self.workout_steps = busy_workout
        else:  # workout
            self.busy_blocks = workout_busy
            self.workout_steps = workout_workout
        
        # Initialize hunger and fullness
        self.hunger = 0.3  # Wake up moderately hungry
        self.fullness = 0.0
        
        # Reset timestep
        self.current_step = 0
        
        # Clear meal history
        self.meals_eaten = 0
        self.snacks_eaten = 0
        self.last_meal_step = -self.total_steps  # Start with maximum time since last meal
        
        # Set macro remaining to full targets
        self.calories_remaining = self.target_calories
        self.protein_remaining = self.target_protein
        self.carbs_remaining = self.target_carbs
        self.fat_remaining = self.target_fat
        
        # Reset consumed macros
        self.calories_consumed = 0
        self.protein_consumed = 0
        self.carbs_consumed = 0
        self.fat_consumed = 0
        
        # Set calories burned to 0
        self.calories_burned = 0
        
        # Reset fullness timers
        self.fullness_cooldown = 0
        
        return self._get_obs(), {}
    
    def _get_obs(self):
        """
        Build and return the 13-value observation state vector.
        
        Returns:
            np.array: 13-value observation state vector
        """
        state = np.array([
            self.hunger,                                      # 0: hunger [0-1]
            self.fullness,                                    # 1: fullness [0-1]
            self.current_step / self.total_steps,            # 2: progress through day [0-1]
            (self.current_step - self.last_meal_step) / self.total_steps,   # 3: time since last meal [0-1]
            self.calories_remaining / self.target_calories,   # 4: calories remaining normalized [-inf, inf]
            self.protein_remaining / self.target_protein,     # 5: protein remaining normalized [-inf, inf]
            self.carbs_remaining / self.target_carbs,         # 6: carbs remaining normalized [-inf, inf]
            self.fullness_cooldown / self.meal_fullness_duration,        # 7: fullness cooldown [0-1]
            self._steps_until_next_busy() / self.total_steps,           # 8: steps until next busy block [0-1]
            self.calories_burned / 1000,                      # 9: calories burned normalized [0-1]
            self.meals_eaten / 4,                             # 10: meals eaten count normalized [0-1]
            self.snacks_eaten / 8,                            # 11: snacks eaten count normalized [0-1]
            self.fat_remaining / self.target_fat              # 12: fat remaining normalized [-inf, inf]
        ], dtype=np.float32)
        
        return state
    
    def _steps_until_next_busy(self):
        """
        Calculate steps until the next busy block.
        
        Returns:
            int: Steps until next busy block, or total_steps if none remaining
        """
        next_busy = next((b for b in sorted(self.busy_blocks) if b > self.current_step), self.total_steps)
        return next_busy - self.current_step
    
    def _update_hunger_fullness(self, is_workout_step):
        """
        Update hunger and fullness each timestep.
        
        Args:
            is_workout_step (bool): Whether the current step is a workout step
        """
        # Decay fullness by base rate
        fullness_decay = 0.10
        
        # Faster decay during workout steps
        if is_workout_step:
            fullness_decay = 0.15
        
        # Apply decay and clamp fullness to minimum 0
        self.fullness = max(0.0, self.fullness - fullness_decay)
        
        # Decrement fullness cooldown
        if self.fullness_cooldown > 0:
            self.fullness_cooldown -= 1
        
        # Hunger rises as fullness falls
        # Simplest version: hunger = 1 - fullness, capped at 1.0
        self.hunger = min(1.0, 1.0 - self.fullness)
    
    def _apply_meal(self, meal_type):
        """
        Apply the effects of eating a meal or snack.
        
        Args:
            meal_type (str): Either 'snack' or 'meal'
        """
        if meal_type == 'snack':
            # Snack: moderate fullness boost
            self.fullness = 0.5
            self.fullness_cooldown = 3  # Single cooldown
            self.snacks_eaten += 1
            
            # Placeholder macro contribution for a snack
            # TODO: Replace with real food database lookup
            meal_calories = 150
            meal_protein = 5
            meal_carbs = 20
            meal_fat = 5
            
        elif meal_type == 'meal':
            # Meal: significant fullness boost
            self.fullness = 0.9
            self.fullness_cooldown = 6  # Single cooldown
            self.meals_eaten += 1
            
            # Placeholder macro contribution for a meal
            # TODO: Replace with real food database lookup
            meal_calories = 600
            meal_protein = 40
            meal_carbs = 60
            meal_fat = 20
        
        # Update consumed macros
        self.calories_consumed += meal_calories
        self.protein_consumed += meal_protein
        self.carbs_consumed += meal_carbs
        self.fat_consumed += meal_fat
        
        # Update remaining macros
        self.calories_remaining = self.target_calories - self.calories_consumed
        self.protein_remaining = self.target_protein - self.protein_consumed
        self.carbs_remaining = self.target_carbs - self.carbs_consumed
        self.fat_remaining = self.target_fat - self.fat_consumed
        
        # Update last meal step
        self.last_meal_step = self.current_step
        
    def step(self, action):
        """
        Execute one timestep in the environment.
        
        Args:
            action (int): The action to take (0=wait, 1=snack, 2=meal)
            
        Returns:
            tuple: (observation, reward, done, truncated, info)
        """
        # Increment timestep
        self.current_step += 1
        
        # Check if action is valid
        is_busy = self.current_step in self.busy_blocks
        is_on_cooldown = self.fullness_cooldown > 0
        
        if is_busy or is_on_cooldown:
            action = 0  # Override to wait
        
        # Apply meal if action is 1 (snack) or 2 (meal)
        if action == 1:
            self._apply_meal('snack')
        elif action == 2:
            self._apply_meal('meal')
        
        # Update hunger and fullness
        is_workout_step = self.current_step in self.workout_steps
        self._update_hunger_fullness(is_workout_step)
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if done
        done = self.current_step >= self.total_steps
        
        # Return observation, reward, done, truncated, info
        return self._get_obs(), reward, done, False, {}

    def _calculate_reward(self):
        """
        Calculate the reward for the current state.
        
        Returns:
            float: The reward value
        """
        reward = 0.0
        
        # Subtract hunger penalty per step
        reward -= self.hunger * 0.1
        
        # At end of day only: macro target rewards
        if self.current_step >= self.total_steps:
            # Calculate how close each macro is to target
            macros = [
                (self.calories_consumed, self.target_calories),
                (self.protein_consumed, self.target_protein),
                (self.carbs_consumed, self.target_carbs),
                (self.fat_consumed, self.target_fat)
            ]
            
            for consumed, target in macros:
                if target > 0:
                    # Proportional reward: closer to target = higher reward
                    deviation = abs(consumed - target) / target
                    macro_reward = 1.0 - deviation  # 1.0 for perfect, 0.0 for 100% deviation
                    reward += macro_reward
        
        return reward
