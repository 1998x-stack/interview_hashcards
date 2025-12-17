"""
FSRS Scheduler - Free Spaced Repetition Scheduler
Implements the state-of-the-art scheduling algorithm

Based on: https://github.com/open-spaced-repetition/fsrs4anki
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum
import math


class Rating(IntEnum):
    """User ratings for card review"""
    AGAIN = 1    # Complete failure
    HARD = 2     # Incorrect but recalled with effort
    GOOD = 3     # Correct with some effort
    EASY = 4     # Perfect recall


class State(IntEnum):
    """Card learning state"""
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


@dataclass
class CardSchedule:
    """Scheduling information for a card"""
    card_hash: str
    state: State
    stability: float  # Memory stability (days)
    difficulty: float  # Card difficulty (0-10)
    elapsed_days: int  # Days since last review
    scheduled_days: int  # Days until next review
    reps: int  # Number of reviews
    lapses: int  # Number of times forgotten
    last_review: Optional[datetime]
    due: datetime


@dataclass
class ReviewLog:
    """Record of a single review"""
    card_hash: str
    rating: Rating
    state: State
    review_time: datetime
    scheduled_days: int
    elapsed_days: int


class FSRSScheduler:
    """
    FSRS (Free Spaced Repetition Scheduler) implementation
    
    Core algorithm:
    - Stability (S): How long until forgetting probability reaches threshold
    - Difficulty (D): Inherent card difficulty
    - Retrievability (R): Current memory strength
    
    Unlike SM-2's fixed intervals, FSRS adapts to individual card difficulty
    """
    
    # Default FSRS parameters (optimized for general learning)
    DEFAULT_PARAMS = {
        'w': [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61],
        'request_retention': 0.9,  # Target 90% retention
        'maximum_interval': 36500,  # 100 years
        'learning_steps': [1, 10],  # 1 min, 10 min for new cards
        'relearning_steps': [10],  # 10 min for forgotten cards
    }
    
    def __init__(self, params: Optional[dict] = None):
        """Initialize scheduler with parameters"""
        self.params = params or self.DEFAULT_PARAMS.copy()
        self.w = self.params['w']
    
    def init_card(self, card_hash: str) -> CardSchedule:
        """Initialize a new card"""
        return CardSchedule(
            card_hash=card_hash,
            state=State.NEW,
            stability=0.0,
            difficulty=5.0,  # Start at medium difficulty
            elapsed_days=0,
            scheduled_days=0,
            reps=0,
            lapses=0,
            last_review=None,
            due=datetime.now()
        )
    
    def review_card(self, schedule: CardSchedule, rating: Rating) -> tuple[CardSchedule, ReviewLog]:
        """
        Process a card review and update schedule
        
        Args:
            schedule: Current card schedule
            rating: User's rating
            
        Returns:
            (updated_schedule, review_log)
        """
        now = datetime.now()
        elapsed_days = 0
        
        if schedule.last_review:
            elapsed_days = (now - schedule.last_review).days
        
        # Create review log
        log = ReviewLog(
            card_hash=schedule.card_hash,
            rating=rating,
            state=schedule.state,
            review_time=now,
            scheduled_days=schedule.scheduled_days,
            elapsed_days=elapsed_days
        )
        
        # Update schedule based on state
        if schedule.state == State.NEW:
            new_schedule = self._review_new_card(schedule, rating, now)
        elif schedule.state == State.LEARNING or schedule.state == State.RELEARNING:
            new_schedule = self._review_learning_card(schedule, rating, now, elapsed_days)
        else:  # REVIEW state
            new_schedule = self._review_review_card(schedule, rating, now, elapsed_days)
        
        return new_schedule, log
    
    def _review_new_card(self, schedule: CardSchedule, rating: Rating, now: datetime) -> CardSchedule:
        """Handle review of a new card"""
        schedule = CardSchedule(**schedule.__dict__)  # Copy
        schedule.reps = 1
        schedule.last_review = now
        
        # Initialize difficulty based on first rating
        schedule.difficulty = self._init_difficulty(rating)
        
        if rating == Rating.AGAIN:
            schedule.state = State.LEARNING
            schedule.scheduled_days = 0
            schedule.due = now + timedelta(minutes=self.params['learning_steps'][0])
        else:
            # Calculate initial stability
            schedule.stability = self._init_stability(rating)
            schedule.state = State.REVIEW
            schedule.scheduled_days = self._next_interval(schedule.stability)
            schedule.due = now + timedelta(days=schedule.scheduled_days)
        
        return schedule
    
    def _review_learning_card(self, schedule: CardSchedule, rating: Rating, 
                             now: datetime, elapsed_days: int) -> CardSchedule:
        """Handle review of a learning card"""
        schedule = CardSchedule(**schedule.__dict__)
        schedule.reps += 1
        schedule.last_review = now
        schedule.elapsed_days = elapsed_days
        
        if rating == Rating.AGAIN:
            # Restart learning
            schedule.scheduled_days = 0
            schedule.due = now + timedelta(minutes=self.params['learning_steps'][0])
        elif rating in [Rating.HARD, Rating.GOOD, Rating.EASY]:
            # Graduate to review
            schedule.stability = self._init_stability(rating)
            schedule.state = State.REVIEW
            schedule.scheduled_days = self._next_interval(schedule.stability)
            schedule.due = now + timedelta(days=schedule.scheduled_days)
        
        return schedule
    
    def _review_review_card(self, schedule: CardSchedule, rating: Rating,
                           now: datetime, elapsed_days: int) -> CardSchedule:
        """Handle review of a mature card"""
        schedule = CardSchedule(**schedule.__dict__)
        schedule.reps += 1
        schedule.last_review = now
        schedule.elapsed_days = elapsed_days
        
        # Calculate retrievability (memory strength)
        retrievability = self._calculate_retrievability(schedule.stability, elapsed_days)
        
        if rating == Rating.AGAIN:
            # Card forgotten - move to relearning
            schedule.state = State.RELEARNING
            schedule.lapses += 1
            schedule.stability = self._next_stability_after_failure(schedule, retrievability)
            schedule.scheduled_days = 0
            schedule.due = now + timedelta(minutes=self.params['relearning_steps'][0])
        else:
            # Card remembered - update parameters
            schedule.stability = self._next_stability_after_success(schedule, rating, retrievability)
            schedule.difficulty = self._next_difficulty(schedule.difficulty, rating)
            schedule.scheduled_days = self._next_interval(schedule.stability)
            schedule.due = now + timedelta(days=schedule.scheduled_days)
        
        return schedule
    
    def _init_difficulty(self, rating: Rating) -> float:
        """Initialize difficulty based on first rating"""
        return self.w[4] - (rating - 3) * self.w[5]
    
    def _init_stability(self, rating: Rating) -> float:
        """Initialize stability based on first successful rating"""
        return self.w[rating - 1]
    
    def _next_difficulty(self, difficulty: float, rating: Rating) -> float:
        """Update difficulty based on rating"""
        next_d = difficulty - self.w[6] * (rating - 3)
        return max(1, min(10, next_d))  # Clamp to [1, 10]
    
    def _calculate_retrievability(self, stability: float, elapsed_days: int) -> float:
        """Calculate current memory retrievability"""
        return math.pow(1 + elapsed_days / (9 * stability), -1)
    
    def _next_stability_after_success(self, schedule: CardSchedule, 
                                     rating: Rating, retrievability: float) -> float:
        """Calculate next stability after successful recall"""
        hard_penalty = self.w[15] if rating == Rating.HARD else 1
        easy_bonus = self.w[16] if rating == Rating.EASY else 1
        
        new_stability = schedule.stability * (
            1 + math.exp(self.w[8]) *
            (11 - schedule.difficulty) *
            math.pow(schedule.stability, -self.w[9]) *
            (math.exp((1 - retrievability) * self.w[10]) - 1) *
            hard_penalty *
            easy_bonus
        )
        
        return new_stability
    
    def _next_stability_after_failure(self, schedule: CardSchedule, 
                                     retrievability: float) -> float:
        """Calculate next stability after forgetting"""
        new_stability = (
            self.w[11] *
            math.pow(schedule.difficulty, -self.w[12]) *
            (math.pow(schedule.stability + 1, self.w[13]) - 1) *
            math.exp((1 - retrievability) * self.w[14])
        )
        return max(0.1, new_stability)  # Minimum stability
    
    def _next_interval(self, stability: float) -> int:
        """Calculate next review interval in days"""
        interval = stability * (
            math.log(self.params['request_retention']) / math.log(0.9)
        )
        interval = min(interval, self.params['maximum_interval'])
        return max(1, round(interval))