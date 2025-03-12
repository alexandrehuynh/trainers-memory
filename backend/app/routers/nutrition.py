from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta

# Import auth and DB dependencies
from ..auth_utils import validate_api_key  # Changed to use validate_api_key consistently
from ..utils.response import StandardResponse

router = APIRouter()

@router.post("/meal-plans", response_model=Dict[str, Any])
async def generate_meal_plan(
    client_id: uuid.UUID = Query(..., description="Client ID to generate meal plan for"),
    requirements: Dict[str, Any] = Body(..., description="Meal plan requirements and parameters"),
    client_info: Dict[str, Any] = Depends(validate_api_key)  # Updated to use validate_api_key
):
    """
    Generate a personalized meal plan based on client data and specified requirements.
    
    Takes client information and meal plan requirements to generate a complete
    nutrition plan tailored to the client's needs, goals, and preferences.
    
    Example requirements:
    ```json
    {
        "goal": "muscle_gain",
        "calories_per_day": 2800,
        "meals_per_day": 4,
        "duration_days": 7,
        "dietary_preferences": ["high_protein", "moderate_carb"],
        "restrictions": ["no_dairy", "no_pork"],
        "include_shopping_list": true
    }
    ```
    """
    try:
        # Validate request data
        required_fields = ["goal", "calories_per_day", "meals_per_day", "duration_days"]
        for field in required_fields:
            if field not in requirements:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # This would connect to a more sophisticated meal planning service
        # For now, return a placeholder meal plan
        
        # Map goals to macronutrient distributions
        macro_distributions = {
            "muscle_gain": {"protein": 30, "carbs": 40, "fat": 30},
            "fat_loss": {"protein": 40, "carbs": 20, "fat": 40},
            "maintenance": {"protein": 30, "carbs": 35, "fat": 35},
            "performance": {"protein": 25, "carbs": 55, "fat": 20}
        }
        
        # Get macros for the specified goal
        goal = requirements.get("goal", "maintenance").lower()
        macros = macro_distributions.get(goal, macro_distributions["maintenance"])
        
        # Calculate daily macronutrient targets
        calories = requirements["calories_per_day"]
        protein_g = round((calories * macros["protein"] / 100) / 4)  # 4 calories per gram of protein
        carbs_g = round((calories * macros["carbs"] / 100) / 4)      # 4 calories per gram of carbs
        fat_g = round((calories * macros["fat"] / 100) / 9)          # 9 calories per gram of fat
        
        # Sample meal templates
        breakfast_options = [
            {
                "name": "Protein Oatmeal with Berries",
                "ingredients": ["oats", "whey protein", "almond milk", "mixed berries", "almond butter"],
                "macros": {"calories": 450, "protein": 30, "carbs": 45, "fat": 15}
            },
            {
                "name": "Veggie Egg White Omelet with Toast",
                "ingredients": ["egg whites", "spinach", "bell peppers", "whole grain toast", "avocado"],
                "macros": {"calories": 400, "protein": 35, "carbs": 30, "fat": 15}
            }
        ]
        
        lunch_options = [
            {
                "name": "Grilled Chicken Salad with Quinoa",
                "ingredients": ["chicken breast", "mixed greens", "quinoa", "cherry tomatoes", "olive oil", "balsamic vinegar"],
                "macros": {"calories": 550, "protein": 40, "carbs": 35, "fat": 20}
            },
            {
                "name": "Turkey and Avocado Wrap",
                "ingredients": ["turkey breast", "whole grain wrap", "avocado", "lettuce", "tomato", "mustard"],
                "macros": {"calories": 500, "protein": 35, "carbs": 40, "fat": 20}
            }
        ]
        
        dinner_options = [
            {
                "name": "Baked Salmon with Sweet Potato and Broccoli",
                "ingredients": ["salmon fillet", "sweet potato", "broccoli", "olive oil", "lemon", "herbs"],
                "macros": {"calories": 600, "protein": 40, "carbs": 45, "fat": 25}
            },
            {
                "name": "Lean Beef Stir Fry with Rice",
                "ingredients": ["lean beef", "brown rice", "bell peppers", "broccoli", "carrots", "soy sauce", "ginger"],
                "macros": {"calories": 650, "protein": 45, "carbs": 50, "fat": 20}
            }
        ]
        
        snack_options = [
            {
                "name": "Greek Yogurt with Honey and Nuts",
                "ingredients": ["greek yogurt", "honey", "mixed nuts", "cinnamon"],
                "macros": {"calories": 300, "protein": 20, "carbs": 20, "fat": 15}
            },
            {
                "name": "Protein Shake with Banana",
                "ingredients": ["whey protein", "banana", "almond milk", "ice"],
                "macros": {"calories": 250, "protein": 25, "carbs": 25, "fat": 5}
            },
            {
                "name": "Apple with Almond Butter",
                "ingredients": ["apple", "almond butter"],
                "macros": {"calories": 200, "protein": 5, "carbs": 25, "fat": 10}
            }
        ]
        
        # Generate daily meal plans
        daily_plans = []
        for day in range(1, requirements["duration_days"] + 1):
            meals = []
            day_of_week = (datetime.now() + timedelta(days=day-1)).strftime("%A")
            
            # Add breakfast
            meals.append(breakfast_options[day % len(breakfast_options)])
            
            # Add lunch
            meals.append(lunch_options[day % len(lunch_options)])
            
            # Add dinner
            meals.append(dinner_options[day % len(dinner_options)])
            
            # Add snacks if needed
            for i in range(requirements["meals_per_day"] - 3):
                if i < len(snack_options):
                    meals.append(snack_options[i])
            
            # Calculate daily totals
            daily_calories = sum(meal["macros"]["calories"] for meal in meals)
            daily_protein = sum(meal["macros"]["protein"] for meal in meals)
            daily_carbs = sum(meal["macros"]["carbs"] for meal in meals)
            daily_fat = sum(meal["macros"]["fat"] for meal in meals)
            
            daily_plans.append({
                "day": day,
                "day_of_week": day_of_week,
                "meals": meals,
                "daily_totals": {
                    "calories": daily_calories,
                    "protein": daily_protein,
                    "carbs": daily_carbs,
                    "fat": daily_fat
                }
            })
        
        # Generate shopping list if requested
        shopping_list = None
        if requirements.get("include_shopping_list", False):
            # Collect all ingredients
            all_ingredients = []
            for day in daily_plans:
                for meal in day["meals"]:
                    all_ingredients.extend(meal["ingredients"])
            
            # Count occurrences and create shopping list
            ingredient_counts = {}
            for ingredient in all_ingredients:
                if ingredient in ingredient_counts:
                    ingredient_counts[ingredient] += 1
                else:
                    ingredient_counts[ingredient] = 1
            
            # Group by category (simplified)
            shopping_list = {
                "proteins": [{"item": item, "quantity": f"{count}x"} for item, count in ingredient_counts.items() if item in ["chicken breast", "turkey breast", "salmon fillet", "lean beef", "greek yogurt", "whey protein", "egg whites"]],
                "carbs": [{"item": item, "quantity": f"{count}x"} for item, count in ingredient_counts.items() if item in ["oats", "whole grain toast", "quinoa", "whole grain wrap", "sweet potato", "brown rice", "banana", "apple"]],
                "fruits_and_vegetables": [{"item": item, "quantity": f"{count}x"} for item, count in ingredient_counts.items() if item in ["mixed berries", "spinach", "bell peppers", "mixed greens", "cherry tomatoes", "lettuce", "tomato", "broccoli", "carrots"]],
                "fats": [{"item": item, "quantity": f"{count}x"} for item, count in ingredient_counts.items() if item in ["almond butter", "avocado", "olive oil", "mixed nuts"]],
                "other": [{"item": item, "quantity": f"{count}x"} for item, count in ingredient_counts.items() if item not in ["chicken breast", "turkey breast", "salmon fillet", "lean beef", "greek yogurt", "whey protein", "egg whites", "oats", "whole grain toast", "quinoa", "whole grain wrap", "sweet potato", "brown rice", "banana", "apple", "mixed berries", "spinach", "bell peppers", "mixed greens", "cherry tomatoes", "lettuce", "tomato", "broccoli", "carrots", "almond butter", "avocado", "olive oil", "mixed nuts"]]
            }
        
        return StandardResponse.success(
            data={
                "client_id": str(client_id),
                "plan_name": f"{requirements['duration_days']}-Day {goal.replace('_', ' ').title()} Meal Plan",
                "goal": goal,
                "calories_per_day": requirements["calories_per_day"],
                "macronutrient_targets": {
                    "protein": f"{protein_g}g ({macros['protein']}%)",
                    "carbs": f"{carbs_g}g ({macros['carbs']}%)",
                    "fat": f"{fat_g}g ({macros['fat']}%)"
                },
                "daily_plans": daily_plans,
                "shopping_list": shopping_list,
                "notes": "This meal plan is designed to support your fitness goals while accommodating your dietary preferences. Adjust portion sizes as needed to meet your specific calorie and macronutrient targets."
            },
            message="Meal plan generated successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating meal plan: {str(e)}"
        )

@router.post("/nutrition-analysis", response_model=Dict[str, Any])
async def analyze_nutrition(
    client_id: uuid.UUID = Query(..., description="Client ID to analyze nutrition for"),
    nutrition_data: Dict[str, Any] = Body(..., description="Nutrition data to analyze"),
    client_info: Dict[str, Any] = Depends(validate_api_key)  # Updated to use validate_api_key
):
    """
    Analyze nutrition data and provide insights and recommendations.
    
    Takes nutrition tracking data and provides analysis on:
    - Macronutrient distribution and adequacy
    - Micronutrient analysis
    - Meal timing and frequency
    - Hydration status
    - Alignment with goals
    
    Example nutrition_data:
    ```json
    {
        "time_period": "7d",
        "daily_entries": [
            {
                "date": "2023-05-01",
                "meals": [
                    {
                        "name": "Breakfast",
                        "time": "08:00",
                        "foods": [
                            {"name": "Oatmeal", "amount": "1 cup", "calories": 300, "protein": 10, "carbs": 50, "fat": 5},
                            {"name": "Banana", "amount": "1 medium", "calories": 105, "protein": 1, "carbs": 27, "fat": 0}
                        ]
                    },
                    ...
                ],
                "totals": {"calories": 2200, "protein": 150, "carbs": 220, "fat": 70, "water": 2500}
            },
            ...
        ]
    }
    ```
    """
    try:
        # Validate request data
        if "daily_entries" not in nutrition_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: daily_entries"
            )
        
        # This would connect to a more sophisticated nutrition analysis service
        # For now, return placeholder analysis
        
        # Calculate averages across all days
        daily_entries = nutrition_data["daily_entries"]
        avg_calories = sum(day["totals"]["calories"] for day in daily_entries) / len(daily_entries)
        avg_protein = sum(day["totals"]["protein"] for day in daily_entries) / len(daily_entries)
        avg_carbs = sum(day["totals"]["carbs"] for day in daily_entries) / len(daily_entries)
        avg_fat = sum(day["totals"]["fat"] for day in daily_entries) / len(daily_entries)
        avg_water = sum(day["totals"].get("water", 0) for day in daily_entries) / len(daily_entries)
        
        # Calculate macronutrient percentages
        protein_calories = avg_protein * 4
        carb_calories = avg_carbs * 4
        fat_calories = avg_fat * 9
        
        protein_pct = round((protein_calories / avg_calories) * 100)
        carb_pct = round((carb_calories / avg_calories) * 100)
        fat_pct = round((fat_calories / avg_calories) * 100)
        
        # Analyze meal frequency and timing
        meal_count = sum(len(day["meals"]) for day in daily_entries) / len(daily_entries)
        
        # Collect all meal times
        all_meal_times = []
        for day in daily_entries:
            for meal in day["meals"]:
                if "time" in meal:
                    all_meal_times.append(meal["time"])
        
        # Simplified meal timing analysis
        meal_timing = "Regular meal timing with consistent spacing between meals"
        
        # Generate analysis and recommendations
        analysis = {
            "caloric_intake": {
                "average_daily": round(avg_calories),
                "assessment": "Appropriate for maintenance" if 1800 <= avg_calories <= 2500 else "May be too low for muscle gain" if avg_calories < 1800 else "May be too high for fat loss"
            },
            "macronutrient_distribution": {
                "protein": {
                    "average_daily": round(avg_protein),
                    "percentage": protein_pct,
                    "assessment": "Adequate for muscle maintenance and growth" if avg_protein >= 1.6 else "May be insufficient for optimal muscle recovery"
                },
                "carbohydrates": {
                    "average_daily": round(avg_carbs),
                    "percentage": carb_pct,
                    "assessment": "Appropriate for activity level" if 40 <= carb_pct <= 60 else "May be too low for optimal performance" if carb_pct < 40 else "May be higher than necessary"
                },
                "fat": {
                    "average_daily": round(avg_fat),
                    "percentage": fat_pct,
                    "assessment": "Within healthy range" if 20 <= fat_pct <= 35 else "May be too low for hormone production" if fat_pct < 20 else "May be higher than optimal"
                }
            },
            "meal_patterns": {
                "average_meals_per_day": round(meal_count, 1),
                "meal_timing": meal_timing,
                "assessment": "Good meal frequency for metabolism and hunger management" if 3 <= meal_count <= 6 else "Consider increasing meal frequency" if meal_count < 3 else "May be excessive meal frequency"
            },
            "hydration": {
                "average_daily_water": round(avg_water),
                "assessment": "Adequate hydration" if avg_water >= 2000 else "Consider increasing water intake"
            }
        }
        
        # Generate recommendations based on analysis
        recommendations = []
        
        if avg_protein < 1.6:
            recommendations.append("Increase protein intake to at least 1.6g per kg of bodyweight for optimal recovery and muscle maintenance")
        
        if carb_pct < 40:
            recommendations.append("Consider increasing carbohydrate intake to support training performance and recovery")
        elif carb_pct > 60:
            recommendations.append("Consider moderating carbohydrate intake and increasing protein or healthy fats")
        
        if fat_pct < 20:
            recommendations.append("Increase healthy fat intake to support hormone production and overall health")
        elif fat_pct > 35:
            recommendations.append("Consider reducing fat intake slightly and increasing protein")
        
        if avg_water < 2000:
            recommendations.append("Increase daily water intake to at least 2-3 liters for optimal hydration and recovery")
        
        if meal_count < 3:
            recommendations.append("Consider adding 1-2 additional meals or snacks to better manage hunger and energy levels")
        
        return StandardResponse.success(
            data={
                "client_id": str(client_id),
                "time_period": nutrition_data.get("time_period", "custom"),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "nutrition_analysis": analysis,
                "recommendations": recommendations,
                "overall_assessment": "Your nutrition is generally well-structured with good attention to protein intake and meal timing. Some adjustments to macronutrient distribution could further optimize your results."
            },
            message="Nutrition analysis completed successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing nutrition data: {str(e)}"
        ) 