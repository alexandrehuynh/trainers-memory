from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import os
import uuid

# Import API key dependency and standard response
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
# Import RAG utilities
from ..utils.fitness_data.embedding_tools import get_rag_context, search_fitness_knowledge

# Create router
router = APIRouter()

# Mock database access (to be replaced with actual LLM integration)
class MockLLM:
    @staticmethod
    def analyze_client_history(client_id: str, query: str) -> Dict[str, Any]:
        """Mock LLM analysis of client history"""
        # In a real implementation, this would call an LLM with workouts data
        return {
            "analysis": f"Based on the client's history, they have shown consistent progress in strength training. Their bench press has improved by 15% over the last 3 months, and their squat has improved by 20%. They tend to perform better in morning sessions compared to evening workouts.",
            "data_points": [
                {"date": "2023-01-15", "exercise": "Bench Press", "weight": 135, "reps": 10},
                {"date": "2023-02-15", "exercise": "Bench Press", "weight": 145, "reps": 10},
                {"date": "2023-03-15", "exercise": "Bench Press", "weight": 155, "reps": 10},
            ],
            "recommendations": [
                "Consider increasing bench press weight to 165 lbs",
                "Schedule more morning sessions for optimal performance",
                "Focus on improving consistency in squat depth"
            ]
        }
    
    @staticmethod
    def analyze_progression(client_id: str, exercise: str = None) -> Dict[str, Any]:
        """Mock LLM analysis of progression for a specific exercise or overall"""
        # In a real implementation, this would call an LLM with exercise data
        if exercise:
            return {
                "exercise": exercise,
                "analysis": f"The client has shown steady progression in {exercise} over the past 6 months. They started at 135 lbs and have progressed to 185 lbs for their working sets. Their form has improved significantly, and they've increased their rep range from 8-10 to 10-12.",
                "progression_rate": "7.8% per month",
                "plateaus": ["Mid-February for 3 weeks"],
                "recommendations": [
                    f"Incorporate drop sets to break through the current {exercise} plateau",
                    "Add a variation exercise to target weak points",
                    "Consider periodization to prevent future plateaus"
                ]
            }
        else:
            return {
                "overall_analysis": "The client has shown good progression across all major lifts, with the most improvement in lower body exercises. Upper body progression has been slower but steady.",
                "strongest_exercises": ["Squat", "Deadlift", "Leg Press"],
                "areas_for_improvement": ["Bench Press", "Overhead Press"],
                "recommendations": [
                    "Increase upper body training frequency",
                    "Incorporate more compound pulling movements",
                    "Add targeted shoulder accessory work"
                ]
            }
    
    @staticmethod
    def predict_injury_risk(client_id: str) -> Dict[str, Any]:
        """Mock LLM injury risk prediction"""
        # In a real implementation, this would call an LLM with workout patterns
        return {
            "overall_risk": "Moderate",
            "potential_issues": [
                {
                    "area": "Lower Back",
                    "risk_level": "Moderate",
                    "contributing_factors": [
                        "Imbalance between posterior chain and quadriceps strength",
                        "Rapid increase in deadlift weight (20% in 2 weeks)"
                    ],
                    "recommendations": [
                        "Incorporate more core stabilization exercises",
                        "Slow down deadlift progression to 5-7% per month",
                        "Add glute-focused exercises to balance posterior chain"
                    ]
                }
            ],
            "protective_factors": [
                "Consistent warm-up routine",
                "Good recovery practices",
                "Balanced programming overall"
            ]
        }

# Request models
class ClientHistoryQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, example="Show me their shoulder progress over the past 3 months")

class ProgressionRequest(BaseModel):
    exercise: Optional[str] = Field(None, example="Bench Press")

class RAGEnhancedQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, example="What exercises are best for shoulder rehab?")
    max_context_length: int = Field(2000, description="Maximum context length to use from the fitness knowledge base")

# Endpoints
@router.post("/client-history", response_model=Dict[str, Any])
async def analyze_client_history(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: ClientHistoryQueryRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze a client's workout history using natural language processing.
    
    - **client_id**: The unique identifier of the client
    - **query**: Natural language query about the client's history
    
    Example queries:
    - "Show me Jane's shoulder progress over the past 3 months"
    - "Has John been consistent with his cardio workouts?"
    - "What exercises has Sarah shown the most improvement in?"
    """
    try:
        # Check if client exists
        # In production, this would validate the client exists
        
        query = request.query if request else "Analyze overall progress"
        
        # In a real implementation, this would connect to an LLM service
        # with client workout data as context
        response = MockLLM.analyze_client_history(client_id, query)
        
        return StandardResponse.success(
            data=response,
            message="Client history analysis completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze client history: {str(e)}"
        )

@router.post("/progression", response_model=Dict[str, Any])
async def analyze_progression(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: ProgressionRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze a client's exercise progression and provide recommendations.
    
    - **client_id**: The unique identifier of the client
    - **exercise**: Optional specific exercise to analyze
    
    If no exercise is specified, an overall progression analysis is provided.
    """
    try:
        # Check if client exists
        # In production, this would validate the client exists
        
        exercise = request.exercise if request and request.exercise else None
        
        # In a real implementation, this would connect to an LLM service
        response = MockLLM.analyze_progression(client_id, exercise)
        
        return StandardResponse.success(
            data=response,
            message="Progression analysis completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze progression: {str(e)}"
        )

@router.get("/injury-prevention", response_model=Dict[str, Any])
async def predict_injury_risk(
    client_id: str = Query(..., description="ID of the client to analyze"),
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze workout patterns to identify potential injury risks.
    
    - **client_id**: The unique identifier of the client
    
    This endpoint identifies imbalances, rapid progression, or other risk factors
    that could lead to injuries, and provides preventative recommendations.
    """
    try:
        # Check if client exists
        # In production, this would validate the client exists
        
        # In a real implementation, this would connect to an LLM service
        response = MockLLM.predict_injury_risk(client_id)
        
        return StandardResponse.success(
            data=response,
            message="Injury risk analysis completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze injury risk: {str(e)}"
        )

@router.post("/analyze-training-program", response_model=Dict[str, Any])
async def analyze_training_program(
    program_data: Dict[str, Any] = Body(..., description="The training program data to analyze"),
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze a training program and provide insights and recommendations.
    
    This endpoint evaluates a structured training program and returns insights about:
    - Program balance (muscle groups, intensity, recovery)
    - Progression structure
    - Potential weak points or improvements
    - Alignment with client goals (if provided)
    
    Example program_data:
    ```json
    {
        "name": "12-Week Strength Foundation",
        "client_id": "optional-client-uuid",
        "goal": "Build overall strength and muscle mass",
        "duration_weeks": 12,
        "sessions_per_week": 4,
        "phases": [
            {
                "name": "Foundation Phase",
                "duration_weeks": 4,
                "sessions": [
                    {
                        "name": "Upper Body Push",
                        "exercises": [...]
                    },
                    ...
                ]
            },
            ...
        ]
    }
    ```
    """
    try:
        # Validate request data
        required_fields = ["name", "duration_weeks", "sessions_per_week"]
        for field in required_fields:
            if field not in program_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # This would be connected to a more sophisticated analysis service
        # For now, return placeholder analysis
        analysis = {
            "program_name": program_data["name"],
            "overview": {
                "duration": f"{program_data['duration_weeks']} weeks",
                "frequency": f"{program_data['sessions_per_week']} sessions per week",
                "estimated_volume": "Moderate to High",
                "primary_focus": "Strength development with hypertrophy elements"
            },
            "balance_analysis": {
                "muscle_group_distribution": {
                    "upper_push": "25%",
                    "upper_pull": "25%",
                    "lower_body": "40%",
                    "core": "10%"
                },
                "intensity_distribution": "Well balanced with appropriate progression",
                "recovery_structure": "Adequate rest days and deload planning"
            },
            "strengths": [
                "Good exercise variety",
                "Progressive overload is clearly implemented",
                "Appropriate volume for stated goals"
            ],
            "recommendations": [
                "Consider adding more direct core work in later phases",
                "May benefit from additional mobility work for shoulder health",
                "Consider implementing RPE-based loading for main lifts"
            ],
            "alignment_with_goals": "High - program structure matches stated goals"
        }
        
        return StandardResponse.success(
            data=analysis,
            message="Training program analysis completed successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing training program: {str(e)}"
        )

@router.post("/generate-training-program", response_model=Dict[str, Any])
async def generate_training_program(
    client_id: Optional[uuid.UUID] = Query(None, description="Client ID to generate program for"),
    requirements: Dict[str, Any] = Body(..., description="Program requirements and parameters"),
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Generate a structured training program based on provided requirements.
    
    Takes client information (optional) and program requirements to generate
    a complete training program tailored to those specifications.
    
    Example requirements:
    ```json
    {
        "goal": "Muscle growth and strength",
        "duration_weeks": 8,
        "sessions_per_week": 4,
        "experience_level": "intermediate",
        "available_equipment": ["barbell", "dumbbells", "cable machine", "bodyweight"],
        "focus_areas": ["chest", "back width"],
        "constraints": ["shoulder injury - avoid overhead pressing"]
    }
    ```
    """
    try:
        # Validate request data
        required_fields = ["goal", "duration_weeks", "sessions_per_week", "experience_level"]
        for field in required_fields:
            if field not in requirements:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # This would be connected to a more sophisticated program generation service
        # For now, return a placeholder program template
        today = datetime.now()
        
        # Create program phases
        phases = []
        weeks_per_phase = max(2, requirements["duration_weeks"] // 3)
        remaining_weeks = requirements["duration_weeks"]
        
        # Generate phases (typically 2-3)
        phase_names = ["Foundation Phase", "Development Phase", "Intensification Phase"]
        phase_count = min(3, (requirements["duration_weeks"] + weeks_per_phase - 1) // weeks_per_phase)
        
        for i in range(phase_count):
            phase_duration = min(weeks_per_phase, remaining_weeks)
            remaining_weeks -= phase_duration
            
            # Sample exercises for different workout types
            workouts = []
            workout_templates = [
                {"name": "Upper Body", "focus": ["chest", "back", "shoulders", "arms"]},
                {"name": "Lower Body", "focus": ["quadriceps", "hamstrings", "glutes", "calves"]},
                {"name": "Push", "focus": ["chest", "shoulders", "triceps"]},
                {"name": "Pull", "focus": ["back", "biceps", "rear delts"]},
                {"name": "Full Body", "focus": ["compound movements", "total body stimulus"]}
            ]
            
            # For simplicity, assume we do the same workouts each week
            # In a real implementation, this would be much more sophisticated
            if requirements["sessions_per_week"] <= 3:
                # For lower frequency, use full body sessions
                for j in range(requirements["sessions_per_week"]):
                    workouts.append({
                        "name": f"Full Body {j+1}",
                        "exercises": [
                            {"name": "Barbell Squat", "sets": 4, "reps": "6-8", "intensity": "80% 1RM"},
                            {"name": "Bench Press", "sets": 3, "reps": "8-10", "intensity": "75% 1RM"},
                            {"name": "Barbell Row", "sets": 3, "reps": "8-10", "intensity": "75% 1RM"},
                            {"name": "Romanian Deadlift", "sets": 3, "reps": "8-10", "intensity": "75% 1RM"},
                            {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "10-12", "intensity": "moderate"}
                        ]
                    })
            else:
                # For higher frequency, use split routines
                templates = workout_templates[:requirements["sessions_per_week"]]
                for template in templates:
                    exercises = []
                    if "chest" in template["focus"] or "push" in template["focus"]:
                        exercises.append({"name": "Incline Bench Press", "sets": 3, "reps": "8-10", "intensity": "moderate-heavy"})
                        exercises.append({"name": "Cable Fly", "sets": 3, "reps": "10-12", "intensity": "moderate"})
                    if "back" in template["focus"] or "pull" in template["focus"]:
                        exercises.append({"name": "Pull-Up", "sets": 3, "reps": "8-10", "intensity": "bodyweight"})
                        exercises.append({"name": "Seated Cable Row", "sets": 3, "reps": "10-12", "intensity": "moderate"})
                    if "legs" in template["focus"] or "lower" in template["focus"]:
                        exercises.append({"name": "Barbell Squat", "sets": 4, "reps": "6-8", "intensity": "heavy"})
                        exercises.append({"name": "Romanian Deadlift", "sets": 3, "reps": "8-10", "intensity": "moderate-heavy"})
                    
                    workouts.append({
                        "name": template["name"],
                        "exercises": exercises
                    })
            
            phases.append({
                "name": phase_names[i],
                "duration_weeks": phase_duration,
                "description": f"Focus on {'building foundation' if i == 0 else 'progressive overload' if i == 1 else 'intensity techniques'}",
                "workouts": workouts
            })
        
        program = {
            "name": f"{requirements['duration_weeks']}-Week {requirements['goal']} Program",
            "goal": requirements["goal"],
            "client_id": str(client_id) if client_id else None,
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": (today + timedelta(days=7*requirements["duration_weeks"])).strftime("%Y-%m-%d"),
            "duration_weeks": requirements["duration_weeks"],
            "sessions_per_week": requirements["sessions_per_week"],
            "experience_level": requirements["experience_level"],
            "equipment_needed": requirements.get("available_equipment", ["basic gym equipment"]),
            "phases": phases,
            "notes": "This program includes progressive overload by increasing weight or reps each week. Adjust intensity based on recovery and performance."
        }
        
        return StandardResponse.success(
            data=program,
            message="Training program generated successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating training program: {str(e)}"
        )

@router.post("/exercise-recommendations", response_model=Dict[str, Any])
async def get_exercise_recommendations(
    parameters: Dict[str, Any] = Body(..., description="Parameters for exercise recommendations"),
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Get personalized exercise recommendations based on goals, equipment, and other parameters.
    
    Example parameters:
    ```json
    {
        "muscle_groups": ["chest", "triceps"],
        "equipment_available": ["barbell", "dumbbells", "cables"],
        "experience_level": "intermediate",
        "goal": "hypertrophy",
        "limitations": ["shoulder impingement"]
    }
    ```
    """
    try:
        # Validate request data
        required_fields = ["muscle_groups", "goal"]
        for field in required_fields:
            if field not in parameters:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # This would connect to a sophisticated exercise recommendation engine
        # For now, return placeholder recommendations
        
        # Map goals to rep ranges and intensities
        goal_parameters = {
            "strength": {"rep_range": "3-6", "intensity": "80-90% 1RM", "rest": "3-5 min"},
            "hypertrophy": {"rep_range": "8-12", "intensity": "70-80% 1RM", "rest": "1-2 min"},
            "endurance": {"rep_range": "15-20", "intensity": "50-60% 1RM", "rest": "30-60 sec"},
            "power": {"rep_range": "3-5", "intensity": "70-85% 1RM", "rest": "2-3 min"},
            "general": {"rep_range": "8-15", "intensity": "moderate", "rest": "1-2 min"}
        }
        
        # Get parameters for the specified goal
        goal = parameters.get("goal", "general").lower()
        training_params = goal_parameters.get(goal, goal_parameters["general"])
        
        # Sample exercises by muscle group (highly simplified)
        exercise_database = {
            "chest": [
                {"name": "Bench Press", "equipment": ["barbell"], "level": "beginner"},
                {"name": "Incline Dumbbell Press", "equipment": ["dumbbells"], "level": "beginner"},
                {"name": "Cable Fly", "equipment": ["cables"], "level": "beginner"},
                {"name": "Dips", "equipment": ["bodyweight"], "level": "intermediate"},
                {"name": "Decline Bench Press", "equipment": ["barbell"], "level": "intermediate"}
            ],
            "back": [
                {"name": "Bent Over Row", "equipment": ["barbell"], "level": "beginner"},
                {"name": "Pull-Up", "equipment": ["bodyweight"], "level": "intermediate"},
                {"name": "Lat Pulldown", "equipment": ["cables"], "level": "beginner"},
                {"name": "Single-Arm Dumbbell Row", "equipment": ["dumbbells"], "level": "beginner"},
                {"name": "T-Bar Row", "equipment": ["barbell"], "level": "intermediate"}
            ],
            "legs": [
                {"name": "Barbell Squat", "equipment": ["barbell"], "level": "beginner"},
                {"name": "Romanian Deadlift", "equipment": ["barbell"], "level": "intermediate"},
                {"name": "Leg Press", "equipment": ["machine"], "level": "beginner"},
                {"name": "Walking Lunges", "equipment": ["dumbbells", "bodyweight"], "level": "beginner"},
                {"name": "Leg Extension", "equipment": ["machine"], "level": "beginner"}
            ],
            "shoulders": [
                {"name": "Overhead Press", "equipment": ["barbell"], "level": "intermediate"},
                {"name": "Lateral Raise", "equipment": ["dumbbells"], "level": "beginner"},
                {"name": "Face Pull", "equipment": ["cables"], "level": "beginner"},
                {"name": "Arnold Press", "equipment": ["dumbbells"], "level": "intermediate"},
                {"name": "Upright Row", "equipment": ["barbell", "dumbbells"], "level": "intermediate"}
            ],
            "arms": [
                {"name": "Bicep Curl", "equipment": ["dumbbells", "barbell"], "level": "beginner"},
                {"name": "Tricep Pushdown", "equipment": ["cables"], "level": "beginner"},
                {"name": "Hammer Curl", "equipment": ["dumbbells"], "level": "beginner"},
                {"name": "Skull Crusher", "equipment": ["barbell"], "level": "intermediate"},
                {"name": "Preacher Curl", "equipment": ["barbell", "dumbbells"], "level": "intermediate"}
            ],
            "core": [
                {"name": "Plank", "equipment": ["bodyweight"], "level": "beginner"},
                {"name": "Russian Twist", "equipment": ["bodyweight", "dumbbells"], "level": "beginner"},
                {"name": "Ab Wheel Rollout", "equipment": ["ab wheel"], "level": "intermediate"},
                {"name": "Hanging Leg Raise", "equipment": ["bodyweight"], "level": "intermediate"},
                {"name": "Cable Crunch", "equipment": ["cables"], "level": "beginner"}
            ]
        }
        
        # Filter exercises based on parameters
        recommendations = {}
        equipment_available = parameters.get("equipment_available", ["bodyweight"])
        experience_level = parameters.get("experience_level", "beginner")
        limitations = parameters.get("limitations", [])
        
        for muscle_group in parameters["muscle_groups"]:
            if muscle_group not in exercise_database:
                continue
                
            suitable_exercises = []
            for exercise in exercise_database[muscle_group]:
                # Check if equipment is available
                has_equipment = any(eq in equipment_available for eq in exercise["equipment"])
                
                # Check if appropriate for experience level
                level_appropriate = True
                if experience_level == "beginner" and exercise["level"] == "advanced":
                    level_appropriate = False
                
                # Check for limitations (very simplified)
                has_limitation = False
                if "shoulder impingement" in limitations and exercise["name"] in ["Overhead Press", "Upright Row"]:
                    has_limitation = True
                
                if has_equipment and level_appropriate and not has_limitation:
                    suitable_exercises.append({
                        "name": exercise["name"],
                        "recommended_sets": 3 if goal != "strength" else 5,
                        "recommended_reps": training_params["rep_range"],
                        "intensity": training_params["intensity"],
                        "rest_period": training_params["rest"]
                    })
            
            recommendations[muscle_group] = suitable_exercises[:3]  # Limit to 3 exercises per muscle group
        
        return StandardResponse.success(
            data={
                "goal": goal,
                "training_parameters": training_params,
                "recommendations": recommendations,
                "notes": "These exercises are selected based on your specified equipment, experience level, and any limitations you provided."
            },
            message="Exercise recommendations generated successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating exercise recommendations: {str(e)}"
        )

@router.post("/rag-enhanced-analysis", response_model=Dict[str, Any])
async def rag_enhanced_analysis(
    request: RAGEnhancedQueryRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key)
):
    """
    Analyze fitness queries with RAG (Retrieval Augmented Generation) to enhance
    responses with domain-specific knowledge.
    
    This endpoint retrieves relevant fitness knowledge from the vector database
    and uses it to augment LLM responses for more accurate and detailed fitness information.
    """
    try:
        # Retrieve relevant knowledge from the fitness vector database
        rag_context = get_rag_context(request.query, max_tokens=request.max_context_length)
        knowledge_results = search_fitness_knowledge(request.query, k=5)
        
        # Format the query with the RAG context
        enhanced_prompt = f"""
        As a professional fitness trainer, answer the following question using your expertise
        and the provided fitness knowledge context.
        
        QUESTION: {request.query}
        
        KNOWLEDGE CONTEXT:
        {rag_context}
        
        Provide a detailed, accurate response based on the knowledge provided.
        Include specific exercise recommendations, technique advice, and safety considerations where relevant.
        """
        
        # Create messages for the AI
        messages = [
            {"role": "system", "content": "You are an expert fitness professional with extensive knowledge of exercise science, biomechanics, and training methodologies."},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        # Use the OpenAI client from the analyze_with_openai_cached function
        from ..utils.cache.openai_analysis import analyze_with_openai_cached
        
        # Get the response from OpenAI
        response = analyze_with_openai_cached(
            messages=messages, 
            temperature=0.2,
            force_refresh=False
        )
        
        # Return the enhanced response with metadata about the knowledge sources
        return StandardResponse(
            status="success",
            message="RAG-enhanced analysis completed successfully",
            data={
                "analysis": response["answer"],
                "sources": [
                    {
                        "category": item["metadata"]["category"],
                        "name": item["metadata"].get("name", item["metadata"].get("title", "Unknown")),
                        "relevance_score": item["score"]
                    } for item in knowledge_results
                ],
                "context_used": True if rag_context else False
            }
        ).dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform RAG-enhanced analysis: {str(e)}"
        ) 