"""
Fitness Knowledge Base

This module contains structured fitness domain knowledge including:
1. Common exercises with descriptions, muscle groups, and techniques
2. Training principles and methodologies
3. Fitness terminology and definitions
4. Safety guidelines and best practices
"""

import json
import os
from typing import Dict, List, Any, Optional

# Path to knowledge base files
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
EXERCISES_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "exercises.json")
PRINCIPLES_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "training_principles.json")
TERMINOLOGY_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "terminology.json")
SAFETY_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "safety_guidelines.json")

# In-memory cache of knowledge
_exercises_cache = None
_principles_cache = None
_terminology_cache = None
_safety_cache = None

def _ensure_dir_exists():
    """Ensure the knowledge base directory exists."""
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

def _create_default_exercises():
    """Create a default exercises file if none exists."""
    exercises = [
        {
            "name": "Bench Press",
            "category": "Compound",
            "primary_muscles": ["Chest", "Triceps", "Shoulders"],
            "equipment": ["Barbell", "Bench"],
            "difficulty": "Intermediate",
            "description": "The bench press is a compound exercise that primarily targets the pectoralis major, anterior deltoids, and triceps. Lie on a flat bench with feet on the ground, grasp the barbell with hands slightly wider than shoulder-width apart, lower the bar to mid-chest, then press it back up to full arm extension.",
            "technique_tips": [
                "Keep wrists straight and elbows at about 45-degree angles from the body",
                "Maintain full foot contact with the floor",
                "Keep shoulder blades retracted and tight",
                "Control the descent and press through the mid-foot"
            ],
            "variations": ["Incline Bench Press", "Decline Bench Press", "Dumbbell Bench Press"],
            "progression_metrics": ["Weight", "Reps", "Sets", "Rest Time"]
        },
        {
            "name": "Squat",
            "category": "Compound",
            "primary_muscles": ["Quadriceps", "Glutes", "Hamstrings", "Lower Back"],
            "equipment": ["Barbell", "Squat Rack"],
            "difficulty": "Advanced",
            "description": "The squat is a compound exercise that targets multiple muscle groups including the quadriceps, glutes, hamstrings, and core. Stand with feet shoulder-width apart, barbell across upper back, bend knees and hips to lower body until thighs are parallel to ground, then return to standing position.",
            "technique_tips": [
                "Keep chest up and back straight",
                "Push knees out in line with toes",
                "Distribute weight through mid-foot and heels",
                "Maintain neutral spine position throughout"
            ],
            "variations": ["Front Squat", "Goblet Squat", "Bulgarian Split Squat"],
            "progression_metrics": ["Weight", "Depth", "Reps", "Sets"]
        },
        {
            "name": "Deadlift",
            "category": "Compound",
            "primary_muscles": ["Lower Back", "Glutes", "Hamstrings", "Traps"],
            "equipment": ["Barbell"],
            "difficulty": "Advanced",
            "description": "The deadlift is a compound exercise that works multiple major muscle groups, primarily the lower back, glutes, and hamstrings. Stand with feet hip-width apart, barbell over mid-foot, bend to grasp bar with shoulder-width grip, extend hips and knees to stand upright with bar, then lower bar back to floor with controlled movement.",
            "technique_tips": [
                "Keep back straight and chest up throughout the movement",
                "Start with bar over mid-foot and shoulders over bar",
                "Drive through heels and keep bar close to body",
                "Engage core and lats before lifting"
            ],
            "variations": ["Sumo Deadlift", "Romanian Deadlift", "Trap Bar Deadlift"],
            "progression_metrics": ["Weight", "Reps", "Sets", "Form Consistency"]
        },
        {
            "name": "Pull-up",
            "category": "Compound",
            "primary_muscles": ["Latissimus Dorsi", "Biceps", "Forearms"],
            "equipment": ["Pull-up Bar"],
            "difficulty": "Intermediate",
            "description": "The pull-up is a compound upper body exercise. Hang from a bar with palms facing away from you and hands slightly wider than shoulder width, pull body up until chin is over the bar, then lower back to starting position with control.",
            "technique_tips": [
                "Engage core and maintain slight posterior pelvic tilt",
                "Initiate the movement by depressing the scapulae",
                "Pull elbows down and back",
                "Avoid excessive swinging or kipping"
            ],
            "variations": ["Chin-up", "Wide-grip Pull-up", "Weighted Pull-up"],
            "progression_metrics": ["Reps", "Sets", "Added Weight", "Eccentric Control"]
        },
        {
            "name": "Shoulder Press",
            "category": "Compound",
            "primary_muscles": ["Shoulders", "Triceps", "Upper Chest"],
            "equipment": ["Barbell", "Dumbbells"],
            "difficulty": "Intermediate",
            "description": "The shoulder press is a compound upper body exercise targeting the deltoids, triceps, and upper chest. Stand with feet shoulder-width apart, hold weight at shoulder level, press weight overhead until arms are fully extended, then lower weight back to shoulders.",
            "technique_tips": [
                "Keep core tight and avoid excessive arching in lower back",
                "Press weights directly overhead, not forward",
                "Fully lock out arms at the top of the movement",
                "Control the descent to protect the shoulders"
            ],
            "variations": ["Seated Shoulder Press", "Arnold Press", "Push Press"],
            "progression_metrics": ["Weight", "Reps", "Sets", "Exercise Variation"]
        }
    ]
    
    _ensure_dir_exists()
    with open(EXERCISES_FILE, 'w') as f:
        json.dump(exercises, f, indent=2)
    
    return exercises

def _create_default_principles():
    """Create a default training principles file if none exists."""
    principles = [
        {
            "name": "Progressive Overload",
            "category": "Training Principle",
            "description": "The principle of progressive overload states that to continue making progress, the demands placed on the musculoskeletal system must gradually increase over time. This can be accomplished by increasing weight, reps, sets, frequency, or decreasing rest periods.",
            "application": [
                "Gradually increase weight by 5-10% when current weight becomes manageable",
                "Add 1-2 reps to each set before increasing weight",
                "Add an additional set to exercises as strength improves",
                "Reduce rest periods between sets to increase intensity"
            ],
            "importance": "Progressive overload is the most fundamental principle for continued strength and hypertrophy gains. Without progressive overload, the body has no stimulus to adapt and improve."
        },
        {
            "name": "Specificity",
            "category": "Training Principle",
            "description": "The principle of specificity states that training adaptations are specific to the type of training performed. To improve in a particular exercise, sport, or skill, one must perform that specific activity.",
            "application": [
                "Train similar movement patterns to the target activity",
                "Match energy systems used in training to those required in target activity",
                "Include sport-specific exercises in training programs",
                "Adjust intensity and volume to match the demands of the target activity"
            ],
            "importance": "Specificity ensures that training adaptations transfer effectively to performance goals. Without specificity, training may not lead to improvements in the desired outcomes."
        },
        {
            "name": "Recovery and Supercompensation",
            "category": "Training Principle",
            "description": "The principles of recovery and supercompensation state that after training stress, the body needs time to recover and adapt. With proper recovery, the body supercompensates by becoming stronger or more capable than the pre-training state.",
            "application": [
                "Allow 48-72 hours between training the same muscle group",
                "Include deload weeks every 4-6 weeks of intense training",
                "Prioritize sleep, nutrition, and stress management for optimal recovery",
                "Plan training cycles to coincide with supercompensation periods"
            ],
            "importance": "Without adequate recovery, overtraining can occur, leading to decreased performance, increased injury risk, and hormonal imbalances. Proper recovery enables continued progress and adaptation."
        },
        {
            "name": "Variation",
            "category": "Training Principle",
            "description": "The principle of variation states that training programs should include variety to prevent plateaus, reduce injury risk, and maintain motivation. This includes varying exercises, intensity, volume, and training methods.",
            "application": [
                "Rotate between different exercises that target the same muscle groups",
                "Incorporate periodization with distinct phases of training",
                "Vary rep ranges, sets, and intensity across training cycles",
                "Include different training modalities (strength, power, endurance)"
            ],
            "importance": "Variation prevents accommodation, where the body becomes efficient at performing the same exercises, reducing their effectiveness. It also helps maintain psychological interest and reduces repetitive stress injuries."
        },
        {
            "name": "Individualization",
            "category": "Training Principle",
            "description": "The principle of individualization recognizes that each person responds differently to training based on genetics, training history, age, gender, and other factors. Training programs should be tailored to individual needs and responses.",
            "application": [
                "Assess individual strengths, weaknesses, and movement patterns",
                "Adjust training volume and intensity based on recovery capacity",
                "Consider training age and experience when designing programs",
                "Monitor individual progress and adjust programming accordingly"
            ],
            "importance": "Generic programs often fail to address individual needs and limitations. Individualization ensures optimal progress, injury prevention, and sustainable long-term training."
        }
    ]
    
    _ensure_dir_exists()
    with open(PRINCIPLES_FILE, 'w') as f:
        json.dump(principles, f, indent=2)
    
    return principles

def _create_default_terminology():
    """Create a default terminology file if none exists."""
    terminology = [
        {
            "term": "Repetition (Rep)",
            "category": "Training Terminology",
            "definition": "A single complete motion of an exercise, consisting of the concentric (lifting) phase and the eccentric (lowering) phase.",
            "example": "Lowering into a squat and standing back up counts as one repetition of a squat.",
            "related_terms": ["Set", "Range of Motion", "Tempo"]
        },
        {
            "term": "Set",
            "category": "Training Terminology",
            "definition": "A group of consecutive repetitions performed without resting.",
            "example": "Performing 10 push-ups without stopping constitutes one set of push-ups.",
            "related_terms": ["Repetition (Rep)", "Rest Period", "Working Set"]
        },
        {
            "term": "One-Repetition Maximum (1RM)",
            "category": "Training Terminology",
            "definition": "The maximum amount of weight that can be lifted for one complete repetition of an exercise with proper form.",
            "example": "If the heaviest bench press you can perform for one repetition is 225 pounds, your 1RM for the bench press is 225 pounds.",
            "related_terms": ["Strength Training", "Progressive Overload", "Testing"]
        },
        {
            "term": "Hypertrophy",
            "category": "Training Terminology",
            "definition": "The increase in muscle size due to an increase in the size of existing muscle fibers, primarily resulting from resistance training.",
            "example": "Bodybuilders focus on hypertrophy training to maximize muscle size rather than just strength.",
            "related_terms": ["Muscle Growth", "Sarcoplasmic Hypertrophy", "Myofibrillar Hypertrophy"]
        },
        {
            "term": "DOMS (Delayed Onset Muscle Soreness)",
            "category": "Training Terminology",
            "definition": "Muscle pain and stiffness that develops 24-72 hours after exercise, particularly after new or intense workouts.",
            "example": "After performing squats for the first time in months, you may experience DOMS in your quadriceps and glutes for several days afterward.",
            "related_terms": ["Recovery", "Muscle Damage", "Inflammation"]
        }
    ]
    
    _ensure_dir_exists()
    with open(TERMINOLOGY_FILE, 'w') as f:
        json.dump(terminology, f, indent=2)
    
    return terminology

def _create_default_safety():
    """Create a default safety guidelines file if none exists."""
    safety = [
        {
            "title": "Proper Warm-up Protocol",
            "category": "Safety",
            "description": "A proper warm-up increases blood flow to muscles, enhances nervous system activation, and prepares the body for exercise, reducing injury risk.",
            "guidelines": [
                "Begin with 5-10 minutes of light cardiovascular activity",
                "Perform dynamic stretches specific to the planned workout",
                "Include activation exercises for key stabilizing muscles",
                "Perform gradually increasing warm-up sets before heavy lifting"
            ],
            "importance": "High - Skipping warm-up significantly increases injury risk, especially during high-intensity or heavy resistance training."
        },
        {
            "title": "Spotting and Safety Equipment",
            "category": "Safety",
            "description": "Proper spotting techniques and safety equipment use are essential for preventing injuries during resistance training, particularly for exercises that could result in being trapped under weights.",
            "guidelines": [
                "Always use spotters for near-maximal lifts on exercises like bench press and squats",
                "Learn proper spotting techniques for different exercises",
                "Use safety pins or straps in power racks when training alone",
                "Communicate clearly with spotters about rep goals and assistance needs"
            ],
            "importance": "Critical - Proper spotting and safety equipment can prevent catastrophic injuries or death."
        },
        {
            "title": "Exercise Form and Technique",
            "category": "Safety",
            "description": "Proper exercise technique ensures that stress is placed on the intended muscles rather than joints or connective tissues, reducing injury risk and increasing exercise effectiveness.",
            "guidelines": [
                "Learn proper technique before adding significant resistance",
                "Start with bodyweight or light resistance to master movement patterns",
                "Consider working with a qualified trainer for form assessment",
                "Avoid sacrificing form to lift heavier weights or perform more repetitions"
            ],
            "importance": "High - Poor form can lead to acute injuries and chronic pain conditions over time."
        },
        {
            "title": "Training Load Management",
            "category": "Safety",
            "description": "Appropriate management of training volume, intensity, and progression is essential for preventing overtraining, overuse injuries, and ensuring consistent progress.",
            "guidelines": [
                "Follow progressive overload principles with gradual weight increases (5-10%)",
                "Include deload weeks every 4-6 weeks of intense training",
                "Monitor fatigue levels and adjust training accordingly",
                "Allow 48-72 hours of recovery between training the same muscle group"
            ],
            "importance": "Medium-High - Poor load management can lead to overtraining syndrome, decreased performance, and increased injury risk."
        },
        {
            "title": "Exercise Selection and Modification",
            "category": "Safety",
            "description": "Selecting appropriate exercises based on individual capabilities and limitations is crucial for safety and effectiveness in training programs.",
            "guidelines": [
                "Consider individual mobility, stability, and injury history when selecting exercises",
                "Modify exercises as needed for limitations (e.g., using dumbbells instead of barbell)",
                "Progress from simpler to more complex movements as skill develops",
                "Include exercises that address individual movement deficiencies"
            ],
            "importance": "Medium-High - Inappropriate exercise selection can exacerbate existing issues or create new ones."
        }
    ]
    
    _ensure_dir_exists()
    with open(SAFETY_FILE, 'w') as f:
        json.dump(safety, f, indent=2)
    
    return safety

def load_fitness_knowledge():
    """Load all fitness knowledge or create default data if not available.
    
    Returns:
        Dictionary containing all fitness knowledge
    """
    global _exercises_cache, _principles_cache, _terminology_cache, _safety_cache
    
    # Load exercises
    if _exercises_cache is None:
        try:
            if os.path.exists(EXERCISES_FILE):
                with open(EXERCISES_FILE, 'r') as f:
                    _exercises_cache = json.load(f)
            else:
                _exercises_cache = _create_default_exercises()
        except Exception as e:
            print(f"Error loading exercises: {str(e)}")
            _exercises_cache = _create_default_exercises()
    
    # Load principles
    if _principles_cache is None:
        try:
            if os.path.exists(PRINCIPLES_FILE):
                with open(PRINCIPLES_FILE, 'r') as f:
                    _principles_cache = json.load(f)
            else:
                _principles_cache = _create_default_principles()
        except Exception as e:
            print(f"Error loading principles: {str(e)}")
            _principles_cache = _create_default_principles()
    
    # Load terminology
    if _terminology_cache is None:
        try:
            if os.path.exists(TERMINOLOGY_FILE):
                with open(TERMINOLOGY_FILE, 'r') as f:
                    _terminology_cache = json.load(f)
            else:
                _terminology_cache = _create_default_terminology()
        except Exception as e:
            print(f"Error loading terminology: {str(e)}")
            _terminology_cache = _create_default_terminology()
    
    # Load safety
    if _safety_cache is None:
        try:
            if os.path.exists(SAFETY_FILE):
                with open(SAFETY_FILE, 'r') as f:
                    _safety_cache = json.load(f)
            else:
                _safety_cache = _create_default_safety()
        except Exception as e:
            print(f"Error loading safety: {str(e)}")
            _safety_cache = _create_default_safety()
    
    return {
        "exercises": _exercises_cache,
        "principles": _principles_cache,
        "terminology": _terminology_cache,
        "safety": _safety_cache
    }

def get_exercise_info(name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific exercise.
    
    Args:
        name: The name of the exercise to look up
        
    Returns:
        Exercise information or None if not found
    """
    global _exercises_cache
    
    # Ensure exercises are loaded
    if _exercises_cache is None:
        load_fitness_knowledge()
    
    # Search for exercise by name (case-insensitive)
    name_lower = name.lower()
    for exercise in _exercises_cache:
        if exercise["name"].lower() == name_lower:
            return exercise
    
    # Check in variations
    for exercise in _exercises_cache:
        for variation in exercise.get("variations", []):
            if variation.lower() == name_lower:
                # Found a variation, return the main exercise with a note
                result = exercise.copy()
                result["note"] = f"This is a variation of {exercise['name']}"
                return result
    
    return None 