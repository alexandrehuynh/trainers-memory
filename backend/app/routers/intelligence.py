from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks, Body
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

# Import API key dependency and standard response
from ..auth_utils import validate_api_key
from ..utils.response import StandardResponse
# Import RAG utilities
from ..utils.fitness_data.embedding_tools import get_rag_context, search_fitness_knowledge
from ..utils.cache.openai_analysis import analyze_with_openai_cached
from ..db.repositories import AsyncClientRepository, AsyncWorkoutRepository
from ..db.config import get_async_db

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
    force_refresh: bool = Field(False, description="Force refresh the analysis")

class ProgressionRequest(BaseModel):
    exercise: Optional[str] = Field(None, example="Bench Press")
    force_refresh: bool = Field(False, description="Force refresh the analysis")

class RAGEnhancedQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, example="What exercises are best for shoulder rehab?")
    max_context_length: int = Field(2000, description="Maximum context length to use from the fitness knowledge base")
    force_refresh: bool = Field(False, description="Force refresh the analysis")

class PerformanceTrendRequest(BaseModel):
    time_period: str = Field("90d", description="Time period to analyze (30d, 60d, 90d, all)")
    categories: List[str] = Field(default_factory=list, description="Categories to analyze (strength, cardio, flexibility, etc.)")
    force_refresh: bool = Field(False, description="Force refresh the analysis")

class RetentionRiskRequest(BaseModel):
    factors: List[str] = Field(default_factory=list, description="Specific factors to include in risk assessment")
    force_refresh: bool = Field(False, description="Force refresh the analysis")

class ColdStartRecommendationRequest(BaseModel):
    client_id: str = Field(..., example="c1d2e3f4-g5h6-i7j8-k9l0-m1n2o3p4q5r6")
    client_details: Optional[Dict[str, Any]] = Field(None, description="Additional client details if needed")
    force_refresh: bool = Field(False, description="Force refresh the recommendations")

# Endpoints
@router.post("/client-history", response_model=Dict[str, Any])
async def analyze_client_history(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: ClientHistoryQueryRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
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
        # Convert string ID to UUID if needed
        client_uuid = uuid.UUID(client_id) if not isinstance(client_id, uuid.UUID) else client_id
        
        # Get client data from the database
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        client = await client_repo.get_client(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
            
        query = request.query if request else "Analyze overall progress"
        
        # Get client's workout history
        workouts = await workout_repo.get_client_workouts(client_uuid)
        if not workouts:
            return StandardResponse.success(
                data={
                    "analysis": "No workout history found for this client.",
                    "data_points": [],
                    "recommendations": ["Start tracking workouts to get meaningful insights."]
                },
                message="No workout history available"
            )
        
        # Format workout data for LLM
        workout_data = []
        for workout in workouts:
            workout_dict = {
                "date": workout.date.isoformat(),
                "type": workout.workout_type,
                "exercises": []
            }
            
            # Add exercise details if available
            if workout.exercises:
                for exercise in workout.exercises:
                    exercise_dict = {
                        "name": exercise.name,
                        "sets": exercise.sets,
                        "reps": exercise.reps,
                        "weight": exercise.weight,
                        "notes": exercise.notes
                    }
                    workout_dict["exercises"].append(exercise_dict)
            
            workout_data.append(workout_dict)
            
        # Get fitness knowledge context related to the query
        rag_context = get_rag_context(query, max_length=1500)
        
        # Prepare prompt with client data and query
        messages = [
            {"role": "system", "content": f"""You are an AI fitness analysis assistant. 
             You analyze client workout history and provide insights based on the data.
             Use the following fitness knowledge as context for your analysis: {rag_context}
             Respond with detailed insights, data points, and actionable recommendations."""},
            {"role": "user", "content": f"""
             Client name: {client.name}
             Client query: {query}
             
             Client workout history:
             {workout_data}
             
             Please analyze this workout history and provide:
             1. A detailed analysis addressing the query
             2. Key data points that support your analysis
             3. Specific, actionable recommendations for this client
             """}
        ]
        
        # Use the analyze_with_openai_cached function to get response
        llm_response = await analyze_with_openai_cached(
            messages=messages,
            client_id=str(client_uuid),
            query_key=f"client_history:{query}",
            force_refresh=request.force_refresh if request else False
        )
        
        # Process the LLM response
        try:
            analysis_text = llm_response.get("content", "")
            
            # Extract data points and recommendations
            data_points = []
            recommendations = []
            
            # Parse the response to extract structured data
            if "data points:" in analysis_text.lower():
                data_section = analysis_text.lower().split("data points:")[1].split("recommendations:")[0]
                data_points = [point.strip() for point in data_section.split("-") if point.strip()]
            
            if "recommendations:" in analysis_text.lower():
                rec_section = analysis_text.lower().split("recommendations:")[1]
                recommendations = [rec.strip() for rec in rec_section.split("-") if rec.strip()]
            
            response = {
                "analysis": analysis_text,
                "data_points": data_points or [],
                "recommendations": recommendations or []
            }
        except Exception as e:
            # Fallback if parsing fails
            response = {
                "analysis": llm_response.get("content", "Analysis could not be generated"),
                "data_points": [],
                "recommendations": []
            }
        
        return StandardResponse.success(
            data=response,
            message="Client history analysis completed"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Error analyzing client history: {str(e)}",
            error_code=500
        )

@router.post("/progression", response_model=Dict[str, Any])
async def analyze_progression(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: ProgressionRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze a client's exercise progression and provide recommendations.
    
    - **client_id**: The unique identifier of the client
    - **exercise**: Optional specific exercise to analyze
    
    If no exercise is specified, an overall progression analysis is provided.
    """
    try:
        # Convert string ID to UUID if needed
        client_uuid = uuid.UUID(client_id) if not isinstance(client_id, uuid.UUID) else client_id
        
        # Get client data from the database
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        client = await client_repo.get_client(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
            
        exercise = request.exercise if request and request.exercise else None
        
        # Get client's workout history
        workouts = await workout_repo.get_client_workouts(client_uuid)
        if not workouts:
            return StandardResponse.success(
                data={
                    "analysis": "No workout history found for this client.",
                    "progression_rate": "N/A",
                    "plateaus": [],
                    "recommendations": ["Start tracking workouts to get progression insights."]
                },
                message="No workout history available"
            )
        
        # Prepare workout data with exercise focus if specified
        workout_data = []
        for workout in sorted(workouts, key=lambda w: w.date):
            workout_dict = {
                "date": workout.date.isoformat(),
                "exercises": []
            }
            
            # Only include relevant exercises if a specific one was requested
            if workout.exercises:
                for ex in workout.exercises:
                    if not exercise or (exercise and ex.name.lower() == exercise.lower()):
                        exercise_dict = {
                            "name": ex.name,
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "weight": ex.weight,
                            "notes": ex.notes
                        }
                        workout_dict["exercises"].append(exercise_dict)
            
            # Only include workout if it has exercises (after filtering)
            if workout_dict["exercises"]:
                workout_data.append(workout_dict)
        
        if exercise and not any(ex["name"].lower() == exercise.lower() for w in workout_data for ex in w["exercises"]):
            return StandardResponse.success(
                data={
                    "exercise": exercise,
                    "analysis": f"No workout data found for exercise '{exercise}'.",
                    "progression_rate": "N/A",
                    "plateaus": [],
                    "recommendations": [f"Start tracking '{exercise}' to get progression insights."]
                },
                message=f"No data for exercise '{exercise}'"
            )
        
        # Get exercise-specific knowledge context
        query = f"progression analysis for {exercise}" if exercise else "workout progression analysis"
        rag_context = get_rag_context(query, max_length=1500)
        
        # Prepare the prompt for the LLM
        messages = [
            {"role": "system", "content": f"""You are an AI fitness progression analyst. 
             Analyze the client's workout history and provide detailed insights on their progression.
             Use the following fitness knowledge as context: {rag_context}
             
             Focus on:
             1. Performance trends over time
             2. Calculating progression rates (% improvement per month)
             3. Identifying plateaus
             4. Providing actionable recommendations to improve
             
             If analyzing a specific exercise, focus exclusively on that exercise's progression."""},
            {"role": "user", "content": f"""
             Client name: {client.name}
             {f"Exercise to analyze: {exercise}" if exercise else "Analyze overall workout progression"}
             
             Workout history (chronological order):
             {workout_data}
             
             Please provide:
             1. Detailed progression analysis
             2. Monthly progression rate (percentage improvement)
             3. Identification of any plateaus
             4. Specific recommendations to improve progression
             """}
        ]
        
        # Call the LLM with the prompt
        llm_response = await analyze_with_openai_cached(
            messages=messages,
            client_id=str(client_uuid),
            query_key=f"progression:{exercise or 'overall'}",
            force_refresh=request.force_refresh if request else False
        )
        
        # Process and structure the LLM response
        try:
            analysis_text = llm_response.get("content", "")
            
            # Extract structured data from the response
            progression_rate = "Not provided"
            plateaus = []
            recommendations = []
            
            # Parse progression rate
            if "progression rate:" in analysis_text.lower():
                rate_section = analysis_text.lower().split("progression rate:")[1].split("\n")[0]
                progression_rate = rate_section.strip()
            
            # Parse plateaus
            if "plateaus:" in analysis_text.lower():
                plateau_section = analysis_text.lower().split("plateaus:")[1].split("recommendations:")[0]
                plateaus = [p.strip() for p in plateau_section.split("-") if p.strip()]
            
            # Parse recommendations
            if "recommendations:" in analysis_text.lower():
                rec_section = analysis_text.lower().split("recommendations:")[1]
                recommendations = [r.strip() for r in rec_section.split("-") if r.strip()]
            
            response = {
                "exercise": exercise,
                "analysis": analysis_text,
                "progression_rate": progression_rate,
                "plateaus": plateaus or [],
                "recommendations": recommendations or []
            }
        except Exception as e:
            # Fallback if parsing fails
            response = {
                "exercise": exercise,
                "analysis": llm_response.get("content", "Analysis could not be generated"),
                "progression_rate": "Unknown",
                "plateaus": [],
                "recommendations": []
            }
        
        return StandardResponse.success(
            data=response,
            message=f"Progression analysis completed for {exercise or 'overall'}"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Error analyzing progression: {str(e)}",
            error_code=500
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
        
        # Get the response from OpenAI
        response = await analyze_with_openai_cached(
            messages=messages, 
            query_key=f"rag_enhanced:{request.query}",
            temperature=0.2,
            force_refresh=request.force_refresh
        )
        
        # Return the enhanced response with metadata about the knowledge sources
        return StandardResponse(
            status="success",
            message="RAG-enhanced analysis completed successfully",
            data={
                "analysis": response["content"],
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

@router.post("/performance-trends", response_model=Dict[str, Any])
async def detect_performance_trends(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: PerformanceTrendRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze client performance data to detect trends and patterns using AI.
    
    - **client_id**: The unique identifier of the client
    - **time_period**: Time period to analyze (30d, 60d, 90d, all)
    - **categories**: Optional specific performance categories to analyze
    
    This endpoint uses AI pattern recognition to identify trends in client performance data.
    """
    try:
        # Convert string ID to UUID if needed
        client_uuid = uuid.UUID(client_id) if not isinstance(client_id, uuid.UUID) else client_id
        
        # Set defaults if request is None
        if request is None:
            request = PerformanceTrendRequest()
        
        # Get client data from the database
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        client = await client_repo.get_client(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Calculate date range based on time_period
        today = datetime.now().date()
        if request.time_period == "30d":
            start_date = today - timedelta(days=30)
        elif request.time_period == "60d":
            start_date = today - timedelta(days=60)
        elif request.time_period == "90d":
            start_date = today - timedelta(days=90)
        else:  # 'all'
            start_date = None
        
        # Get client's workout history
        workouts = await workout_repo.get_client_workouts(
            client_uuid, 
            start_date=start_date if start_date else None
        )
        
        if not workouts:
            return StandardResponse.success(
                data={
                    "trends": [],
                    "insights": "No workout data available for the selected time period.",
                    "recommendations": ["Start tracking workouts to get trend analysis."]
                },
                message="No workout data available"
            )
        
        # Organize workout data chronologically
        workout_data = []
        for workout in sorted(workouts, key=lambda w: w.date):
            workout_dict = {
                "date": workout.date.isoformat(),
                "type": workout.workout_type,
                "duration": workout.duration,
                "metrics": workout.metrics if hasattr(workout, 'metrics') else {},
                "exercises": []
            }
            
            if workout.exercises:
                for ex in workout.exercises:
                    # Categorize exercises
                    category = "strength"  # Default category
                    if hasattr(ex, 'category') and ex.category:
                        category = ex.category
                    elif ex.name.lower() in ["running", "jogging", "cycling", "swimming", "rowing"]:
                        category = "cardio"
                    elif ex.name.lower() in ["yoga", "stretching", "mobility"]:
                        category = "flexibility"
                    
                    # Only include categories that match the filter (if any)
                    if not request.categories or category in request.categories:
                        exercise_dict = {
                            "name": ex.name,
                            "category": category,
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "weight": ex.weight,
                            "notes": ex.notes
                        }
                        workout_dict["exercises"].append(exercise_dict)
            
            # Only include workout if it has exercises (after filtering)
            if workout_dict["exercises"]:
                workout_data.append(workout_dict)
        
        # Get domain knowledge for context
        rag_context = get_rag_context("workout performance trends pattern recognition", max_length=1500)
        
        # Prepare the prompt for the LLM
        messages = [
            {"role": "system", "content": f"""You are an AI fitness trend analyst specializing in pattern recognition.
             Your task is to analyze workout data over time and identify significant patterns and trends.
             Use the following fitness knowledge as context: {rag_context}
             
             Focus on:
             1. Detecting meaningful patterns in performance data
             2. Identifying correlations between workout variables
             3. Recognizing progress trends and potential issues
             4. Providing data-driven recommendations based on the patterns identified
             
             Your analysis should be detailed and insightful, with specific examples from the data."""},
            {"role": "user", "content": f"""
             Client name: {client.name}
             Time period: {request.time_period}
             Categories to analyze: {request.categories if request.categories else "All categories"}
             
             Workout history (chronological order):
             {workout_data}
             
             Please provide:
             1. A list of detected performance trends with confidence levels
             2. Detailed insights explaining the patterns you've identified
             3. Specific recommendations based on these patterns
             4. Any potential issues or warning signs detected
             """}
        ]
        
        # Call the LLM with the prompt
        llm_response = await analyze_with_openai_cached(
            messages=messages,
            client_id=str(client_uuid),
            query_key=f"trends:{request.time_period}:{'-'.join(request.categories) if request.categories else 'all'}",
            force_refresh=request.force_refresh
        )
        
        # Process and structure the LLM response
        try:
            analysis_text = llm_response.get("content", "")
            
            # Extract structured data
            trends = []
            insights = ""
            recommendations = []
            warnings = []
            
            # Parse trends
            if "trends:" in analysis_text.lower():
                trend_section = analysis_text.lower().split("trends:")[1].split("insights:")[0]
                trend_items = [t.strip() for t in trend_section.split("-") if t.strip()]
                
                for trend in trend_items:
                    trend_obj = {
                        "description": trend,
                        "confidence": "medium"  # Default confidence
                    }
                    
                    # Try to extract confidence level if provided
                    if "confidence:" in trend.lower():
                        trend_parts = trend.lower().split("confidence:")
                        trend_obj["description"] = trend_parts[0].strip()
                        trend_obj["confidence"] = trend_parts[1].strip()
                    
                    trends.append(trend_obj)
            
            # Parse insights
            if "insights:" in analysis_text.lower():
                insight_section = analysis_text.lower().split("insights:")[1].split("recommendations:")[0]
                insights = insight_section.strip()
            
            # Parse recommendations
            if "recommendations:" in analysis_text.lower():
                rec_parts = analysis_text.lower().split("recommendations:")[1]
                rec_section = rec_parts.split("warnings:")[0] if "warnings:" in rec_parts else rec_parts
                recommendations = [r.strip() for r in rec_section.split("-") if r.strip()]
            
            # Parse warnings
            if "warnings:" in analysis_text.lower():
                warning_section = analysis_text.lower().split("warnings:")[1]
                warnings = [w.strip() for w in warning_section.split("-") if w.strip()]
            
            response = {
                "trends": trends,
                "insights": insights,
                "recommendations": recommendations,
                "warnings": warnings
            }
        except Exception as e:
            # Fallback if parsing fails
            response = {
                "trends": [],
                "insights": llm_response.get("content", "Analysis could not be generated"),
                "recommendations": [],
                "warnings": []
            }
        
        return StandardResponse.success(
            data=response,
            message="Performance trend analysis completed"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Error analyzing performance trends: {str(e)}",
            error_code=500
        )

@router.post("/retention-risk", response_model=Dict[str, Any])
async def assess_retention_risk(
    client_id: str = Query(..., description="ID of the client to analyze"),
    request: RetentionRiskRequest = None,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Assess the risk of client churn/attrition and provide retention strategies.
    
    - **client_id**: The unique identifier of the client
    - **factors**: Optional specific factors to include in the risk assessment
    
    This endpoint analyzes client engagement, attendance, progress, and other factors to estimate retention risk.
    """
    try:
        # Convert string ID to UUID if needed
        client_uuid = uuid.UUID(client_id) if not isinstance(client_id, uuid.UUID) else client_id
        
        # Set defaults if request is None
        if request is None:
            request = RetentionRiskRequest()
        
        # Initialize repositories
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        # Get client data
        client = await client_repo.get_client(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client's workout history
        workouts = await workout_repo.get_client_workouts(client_uuid)
        
        # Calculate key metrics
        total_workouts = len(workouts) if workouts else 0
        
        # Attendance patterns
        if workouts:
            # Sort workouts by date
            sorted_workouts = sorted(workouts, key=lambda w: w.date)
            
            # Calculate days since last workout
            last_workout_date = sorted_workouts[-1].date if sorted_workouts else None
            days_since_last_workout = (datetime.now().date() - last_workout_date).days if last_workout_date else None
            
            # Calculate average frequency (days between workouts)
            if len(sorted_workouts) >= 2:
                date_diffs = []
                for i in range(1, len(sorted_workouts)):
                    date_diff = (sorted_workouts[i].date - sorted_workouts[i-1].date).days
                    date_diffs.append(date_diff)
                avg_frequency = sum(date_diffs) / len(date_diffs) if date_diffs else None
            else:
                avg_frequency = None
            
            # Check for declining frequency
            declining_frequency = False
            if len(sorted_workouts) >= 6:
                # Compare first half vs second half frequency
                midpoint = len(sorted_workouts) // 2
                first_half = sorted_workouts[:midpoint]
                second_half = sorted_workouts[midpoint:]
                
                # Calculate frequencies for each half
                first_half_dates = [w.date for w in first_half]
                second_half_dates = [w.date for w in second_half]
                
                if len(first_half_dates) >= 2 and len(second_half_dates) >= 2:
                    first_half_range = (first_half_dates[-1] - first_half_dates[0]).days
                    second_half_range = (second_half_dates[-1] - second_half_dates[0]).days
                    
                    first_half_freq = first_half_range / (len(first_half) - 1) if len(first_half) > 1 else None
                    second_half_freq = second_half_range / (len(second_half) - 1) if len(second_half) > 1 else None
                    
                    # Higher number means more days between workouts (less frequent)
                    declining_frequency = second_half_freq > (first_half_freq * 1.25) if first_half_freq and second_half_freq else False
        else:
            last_workout_date = None
            days_since_last_workout = None
            avg_frequency = None
            declining_frequency = False
        
        # Prepare data for LLM analysis
        client_data = {
            "name": client.name,
            "email": client.email if hasattr(client, 'email') else None,
            "join_date": client.created_at.date().isoformat() if hasattr(client, 'created_at') else None,
            "total_workouts": total_workouts,
            "last_workout_date": last_workout_date.isoformat() if last_workout_date else None,
            "days_since_last_workout": days_since_last_workout,
            "avg_days_between_workouts": avg_frequency,
            "declining_frequency": declining_frequency,
            "cancellation_history": client.cancellation_history if hasattr(client, 'cancellation_history') else None,
            "no_show_count": client.no_show_count if hasattr(client, 'no_show_count') else 0,
            "preferred_workout_times": client.preferred_workout_times if hasattr(client, 'preferred_workout_times') else None,
            "goal_achievement": client.goal_achievement if hasattr(client, 'goal_achievement') else None,
            "satisfaction_scores": client.satisfaction_scores if hasattr(client, 'satisfaction_scores') else None
        }
        
        # Get domain knowledge for context
        rag_context = get_rag_context("client retention fitness industry", max_length=1500)
        
        # Prepare the prompt for the LLM
        messages = [
            {"role": "system", "content": f"""You are an AI specialist in fitness client retention analysis.
             Your task is to assess a client's risk of cancellation or churn, and provide strategies to improve retention.
             Use the following fitness industry knowledge as context: {rag_context}
             
             Focus on:
             1. Identifying early warning signs of potential client churn
             2. Calculating a retention risk score from 1-10 (10 being highest risk)
             3. Analyzing attendance patterns, engagement metrics, and satisfaction indicators
             4. Providing actionable retention strategies based on the client's specific situation
             
             Your analysis should be data-driven and include both qualitative and quantitative elements."""},
            {"role": "user", "content": f"""
             Client data:
             {client_data}
             
             Analyze this client's retention risk based on the provided data.
             Factors to focus on: {request.factors if request.factors else "All relevant factors"}
             
             Please provide:
             1. An overall retention risk score (1-10)
             2. Key risk factors identified
             3. Early warning signs detected
             4. Specific, actionable retention strategies
             5. Recommended communication approach
             """}
        ]
        
        # Call the LLM with the prompt
        llm_response = await analyze_with_openai_cached(
            messages=messages,
            client_id=str(client_uuid),
            query_key=f"retention_risk:{'-'.join(request.factors) if request.factors else 'all'}",
            force_refresh=request.force_refresh
        )
        
        # Process and structure the LLM response
        try:
            analysis_text = llm_response.get("content", "")
            
            # Extract structured data
            risk_score = None
            risk_factors = []
            warning_signs = []
            retention_strategies = []
            communication_approach = ""
            
            # Parse risk score
            if "risk score:" in analysis_text.lower():
                score_text = analysis_text.lower().split("risk score:")[1].split("\n")[0].strip()
                # Try to extract the numeric score
                for word in score_text.split():
                    if word.isdigit() and 1 <= int(word) <= 10:
                        risk_score = int(word)
                        break
                if risk_score is None and "/10" in score_text:
                    # Try another pattern like "8/10"
                    score_match = score_text.split("/10")[0].strip().split()[-1]
                    if score_match.isdigit():
                        risk_score = int(score_match)
            
            # Default score if parsing fails
            if risk_score is None:
                risk_score = 5  # Medium risk as default
            
            # Parse risk factors
            if "risk factors:" in analysis_text.lower():
                factor_section = analysis_text.lower().split("risk factors:")[1].split("warning signs:")[0] \
                    if "warning signs:" in analysis_text.lower() else \
                    analysis_text.lower().split("risk factors:")[1].split("retention strategies:")[0]
                risk_factors = [f.strip() for f in factor_section.split("-") if f.strip()]
            
            # Parse warning signs
            if "warning signs:" in analysis_text.lower():
                warning_section = analysis_text.lower().split("warning signs:")[1].split("retention strategies:")[0]
                warning_signs = [w.strip() for w in warning_section.split("-") if w.strip()]
            
            # Parse retention strategies
            if "retention strategies:" in analysis_text.lower():
                strategy_section = analysis_text.lower().split("retention strategies:")[1].split("communication approach:")[0] \
                    if "communication approach:" in analysis_text.lower() else \
                    analysis_text.lower().split("retention strategies:")[1]
                retention_strategies = [s.strip() for s in strategy_section.split("-") if s.strip()]
            
            # Parse communication approach
            if "communication approach:" in analysis_text.lower():
                comm_section = analysis_text.lower().split("communication approach:")[1]
                communication_approach = comm_section.strip()
            
            response = {
                "risk_score": risk_score,
                "risk_level": "High" if risk_score >= 7 else "Medium" if risk_score >= 4 else "Low",
                "risk_factors": risk_factors,
                "warning_signs": warning_signs,
                "retention_strategies": retention_strategies,
                "communication_approach": communication_approach,
                "analysis": analysis_text
            }
        except Exception as e:
            # Fallback if parsing fails
            response = {
                "risk_score": 5,
                "risk_level": "Medium",
                "risk_factors": [],
                "warning_signs": [],
                "retention_strategies": [],
                "communication_approach": "",
                "analysis": llm_response.get("content", "Analysis could not be generated")
            }
        
        return StandardResponse.success(
            data=response,
            message="Retention risk assessment completed"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Error assessing retention risk: {str(e)}",
            error_code=500
        )

@router.post("/cold-start-recommendations", response_model=Dict[str, Any])
async def get_cold_start_recommendations(
    request: ColdStartRecommendationRequest,
    client_info: Dict[str, Any] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate personalized workout and nutrition recommendations for new clients with limited or no history.
    
    - **client_id**: The unique identifier of the client
    - **client_details**: Optional additional client details to enhance recommendations
    
    This endpoint uses a combination of basic client information, fitness domain knowledge,
    and collaborative filtering concepts to provide relevant startup recommendations.
    """
    try:
        # Convert string ID to UUID if needed
        client_uuid = uuid.UUID(request.client_id) if not isinstance(request.client_id, uuid.UUID) else request.client_id
        
        # Initialize repositories
        client_repo = AsyncClientRepository(db)
        workout_repo = AsyncWorkoutRepository(db)
        
        # Get client data
        client = await client_repo.get_client(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client's workout history (if any)
        workouts = await workout_repo.get_client_workouts(client_uuid)
        
        # Check if this is truly a cold start scenario
        is_cold_start = len(workouts) <= 3  # Consider 3 or fewer workouts as cold start
        
        if not is_cold_start:
            return StandardResponse.success(
                data={
                    "message": "Client has sufficient workout history for regular recommendations.",
                    "workout_count": len(workouts),
                    "recommendation_type": "history_based"
                },
                message="Client has workout history"
            )
        
        # Prepare client profile data
        client_profile = {
            "name": client.name,
            "age": client.age if hasattr(client, 'age') else None,
            "gender": client.gender if hasattr(client, 'gender') else None,
            "height": client.height if hasattr(client, 'height') else None,
            "weight": client.weight if hasattr(client, 'weight') else None,
            "fitness_level": client.fitness_level if hasattr(client, 'fitness_level') else None,
            "goals": client.goals if hasattr(client, 'goals') else None,
            "medical_conditions": client.medical_conditions if hasattr(client, 'medical_conditions') else None,
            "workout_history": [
                {
                    "date": w.date.isoformat(),
                    "type": w.workout_type,
                    "exercises": [{"name": e.name, "sets": e.sets, "reps": e.reps} for e in w.exercises] if hasattr(w, 'exercises') else []
                } for w in workouts
            ],
            # Add any additional details provided in the request
            **(request.client_details or {})
        }
        
        # Get exercise recommendations from third-party databases
        # Use mock data for now, will be replaced with real API calls
        from ..utils.fitness_data.third_party_integration import MockFitnessAPI
        mock_api = MockFitnessAPI()
        
        # Get beginner exercises for different muscle groups
        chest_exercises = await mock_api.get_exercises_by_muscle("chest")
        back_exercises = await mock_api.get_exercises_by_muscle("back")
        leg_exercises = await mock_api.get_exercises_by_muscle("legs")
        
        # Combine exercises from different sources for a varied recommendation
        available_exercises = chest_exercises + back_exercises + leg_exercises
        
        # Get domain knowledge for context
        rag_context = get_rag_context("beginner workout programming new client recommendations", max_length=1500)
        
        # Prepare the prompt for the LLM
        messages = [
            {"role": "system", "content": f"""You are an AI fitness and nutrition advisor specializing in creating 
             recommendations for new clients with limited or no workout history.
             Use the following fitness knowledge as context: {rag_context}
             
             Focus on:
             1. Creating appropriate beginner-friendly workout routines
             2. Suggesting nutrition guidelines based on client goals
             3. Providing progressive plans that can adapt as the client improves
             4. Considering any medical conditions or limitations
             
             Your recommendations should be evidence-based, safe, and tailored to the client's profile."""},
            {"role": "user", "content": f"""
             I need personalized workout and nutrition recommendations for a new client with limited history.
             
             Client profile:
             {client_profile}
             
             Available exercises from database:
             {available_exercises[:15]}  # Limit to 15 exercises for prompt size
             
             Please provide:
             1. A complete 4-week starter workout program with specific exercises, sets, reps
             2. Nutrition guidelines and meal planning suggestions
             3. Supplementary activities to enhance results
             4. Key metrics to track progress
             5. Adaptation strategy as the client progresses
             """}
        ]
        
        # Call the LLM with the prompt
        llm_response = await analyze_with_openai_cached(
            messages=messages,
            client_id=str(client_uuid),
            query_key="cold_start_recommendations",
            force_refresh=request.force_refresh
        )
        
        # Process the LLM response
        try:
            recommendations_text = llm_response.get("content", "")
            
            # Extract structured data sections
            workout_program = ""
            nutrition_guidelines = ""
            supplementary_activities = ""
            tracking_metrics = ""
            adaptation_strategy = ""
            
            # Parse workout program
            if "workout program:" in recommendations_text.lower():
                workout_section = recommendations_text.lower().split("workout program:")[1]
                if "nutrition guidelines:" in workout_section:
                    workout_program = workout_section.split("nutrition guidelines:")[0].strip()
                else:
                    workout_program = workout_section.split("\n\n")[0].strip()
            
            # Parse nutrition guidelines
            if "nutrition guidelines:" in recommendations_text.lower():
                nutrition_section = recommendations_text.lower().split("nutrition guidelines:")[1]
                if "supplementary activities:" in nutrition_section:
                    nutrition_guidelines = nutrition_section.split("supplementary activities:")[0].strip()
                else:
                    nutrition_guidelines = nutrition_section.split("\n\n")[0].strip()
            
            # Parse supplementary activities
            if "supplementary activities:" in recommendations_text.lower():
                activities_section = recommendations_text.lower().split("supplementary activities:")[1]
                if "tracking metrics:" in activities_section:
                    supplementary_activities = activities_section.split("tracking metrics:")[0].strip()
                else:
                    supplementary_activities = activities_section.split("\n\n")[0].strip()
            
            # Parse tracking metrics
            if "tracking metrics:" in recommendations_text.lower():
                metrics_section = recommendations_text.lower().split("tracking metrics:")[1]
                if "adaptation strategy:" in metrics_section:
                    tracking_metrics = metrics_section.split("adaptation strategy:")[0].strip()
                else:
                    tracking_metrics = metrics_section.split("\n\n")[0].strip()
            
            # Parse adaptation strategy
            if "adaptation strategy:" in recommendations_text.lower():
                adaptation_strategy = recommendations_text.lower().split("adaptation strategy:")[1].strip()
            
            response = {
                "workout_program": workout_program,
                "nutrition_guidelines": nutrition_guidelines,
                "supplementary_activities": supplementary_activities,
                "tracking_metrics": tracking_metrics,
                "adaptation_strategy": adaptation_strategy,
                "recommendation_type": "cold_start",
                "full_recommendations": recommendations_text
            }
        except Exception as e:
            # Fallback if parsing fails
            response = {
                "recommendation_type": "cold_start",
                "full_recommendations": llm_response.get("content", "Recommendations could not be generated")
            }
        
        return StandardResponse.success(
            data=response,
            message="Cold start recommendations generated successfully"
        )
    except Exception as e:
        return StandardResponse.error(
            message=f"Error generating cold start recommendations: {str(e)}",
            error_code=500
        ) 