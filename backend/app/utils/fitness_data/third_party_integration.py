"""
Third-Party Fitness Database and Exercise Catalog Integration

This module provides integration with various third-party fitness databases and exercise catalogs:
1. ExerciseDB - A comprehensive exercise database with over 1300 exercises
2. Nutritionix - API for nutrition data and calorie information
3. Wger Workout Manager - Open source workout database
4. OpenFoodFacts - Open database of food products from around the world

Use these integrations to enhance workout recommendations, get exercise details,
nutritional information, and more.
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
import asyncio
from fastapi import HTTPException
import random
from ..cache.api_cache import async_cache_response

# Configure logging
logger = logging.getLogger(__name__)

# Base models
class ExerciseDetails(BaseModel):
    name: str
    muscle_group: str
    equipment: Optional[str] = None
    difficulty: Optional[str] = None
    instructions: Optional[List[str]] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    tips: Optional[List[str]] = None
    variations: Optional[List[str]] = None
    
class NutritionInfo(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    serving_size: str
    serving_unit: str
    
# ExerciseDB integration
class ExerciseDBAPI:
    """Integration with the ExerciseDB API for exercise information"""
    
    BASE_URL = "https://exercisedb.p.rapidapi.com"
    
    def __init__(self):
        self.api_key = os.environ.get("EXERCISEDB_API_KEY", "demo_key")
        self.api_host = "exercisedb.p.rapidapi.com"
        
    async def get_exercises_by_muscle(self, muscle: str) -> List[Dict[str, Any]]:
        """Get exercises by target muscle group"""
        try:
            return await self._make_request(f"/exercises/target/{muscle.lower()}")
        except Exception as e:
            logger.error(f"Error fetching exercises by muscle: {str(e)}")
            return []
            
    async def get_exercises_by_equipment(self, equipment: str) -> List[Dict[str, Any]]:
        """Get exercises by equipment"""
        try:
            return await self._make_request(f"/exercises/equipment/{equipment.lower()}")
        except Exception as e:
            logger.error(f"Error fetching exercises by equipment: {str(e)}")
            return []
            
    async def get_exercise_by_id(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific exercise by ID"""
        try:
            return await self._make_request(f"/exercises/exercise/{exercise_id}")
        except Exception as e:
            logger.error(f"Error fetching exercise by ID: {str(e)}")
            return None
            
    async def search_exercises(self, name: str) -> List[Dict[str, Any]]:
        """Search exercises by name"""
        try:
            return await self._make_request(f"/exercises/name/{name.lower()}")
        except Exception as e:
            logger.error(f"Error searching exercises: {str(e)}")
            return []
    
    @async_cache_response(ttl=86400)  # Cache for 24 hours
    async def _make_request(self, endpoint: str) -> Any:
        """Make a request to the ExerciseDB API with caching"""
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ExerciseDB API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, 
                                   detail=f"ExerciseDB API error: {response.text}")

# Nutritionix integration
class NutritionixAPI:
    """Integration with the Nutritionix API for nutrition information"""
    
    BASE_URL = "https://trackapi.nutritionix.com/v2"
    
    def __init__(self):
        self.app_id = os.environ.get("NUTRITIONIX_APP_ID", "demo_id")
        self.api_key = os.environ.get("NUTRITIONIX_API_KEY", "demo_key")
        
    async def get_nutrition_info(self, query: str) -> List[NutritionInfo]:
        """Get nutrition information for a food item or meal using natural language"""
        try:
            data = {
                "query": query,
                "detailed": True
            }
            
            headers = {
                "x-app-id": self.app_id,
                "x-app-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/natural/nutrients",
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    foods = result.get("foods", [])
                    
                    nutrition_items = []
                    for food in foods:
                        nutrition = NutritionInfo(
                            name=food.get("food_name", "Unknown"),
                            calories=food.get("nf_calories", 0),
                            protein=food.get("nf_protein", 0),
                            carbs=food.get("nf_total_carbohydrate", 0),
                            fat=food.get("nf_total_fat", 0),
                            serving_size=str(food.get("serving_qty", 1)),
                            serving_unit=food.get("serving_unit", "serving")
                        )
                        nutrition_items.append(nutrition)
                    
                    return nutrition_items
                else:
                    logger.error(f"Nutritionix API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching nutrition information: {str(e)}")
            return []
            
    @async_cache_response(ttl=86400)  # Cache for 24 hours
    async def search_food(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for food items"""
        try:
            params = {
                "query": query,
                "detailed": True,
                "limit": limit
            }
            
            headers = {
                "x-app-id": self.app_id,
                "x-app-key": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/instant",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json().get("common", [])
                else:
                    logger.error(f"Nutritionix API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error searching food: {str(e)}")
            return []

# Wger Workout Manager integration
class WgerAPI:
    """Integration with the Wger Workout Manager API"""
    
    BASE_URL = "https://wger.de/api/v2"
    
    @async_cache_response(ttl=86400 * 7)  # Cache for 7 days
    async def get_exercises(self, language: str = "en", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get exercises from Wger"""
        try:
            params = {
                "language": language,
                "limit": limit,
                "offset": offset
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BASE_URL}/exercise", params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Wger API error: {response.status_code} - {response.text}")
                    return {"results": []}
        except Exception as e:
            logger.error(f"Error fetching exercises from Wger: {str(e)}")
            return {"results": []}
    
    @async_cache_response(ttl=86400 * 7)  # Cache for 7 days
    async def get_exercise_categories(self) -> List[Dict[str, Any]]:
        """Get exercise categories from Wger"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BASE_URL}/exercisecategory")
                
                if response.status_code == 200:
                    return response.json().get("results", [])
                else:
                    logger.error(f"Wger API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching exercise categories from Wger: {str(e)}")
            return []
    
    @async_cache_response(ttl=86400 * 7)  # Cache for 7 days
    async def get_muscles(self) -> List[Dict[str, Any]]:
        """Get muscles from Wger"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BASE_URL}/muscle")
                
                if response.status_code == 200:
                    return response.json().get("results", [])
                else:
                    logger.error(f"Wger API error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching muscles from Wger: {str(e)}")
            return []

# OpenFoodFacts integration
class OpenFoodFactsAPI:
    """Integration with the OpenFoodFacts API for food and nutrition data"""
    
    BASE_URL = "https://world.openfoodfacts.org/api/v0"
    
    @async_cache_response(ttl=86400)  # Cache for 24 hours
    async def get_product(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Get product information by barcode"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BASE_URL}/product/{barcode}.json")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1:
                        return data.get("product", {})
                    else:
                        return None
                else:
                    logger.error(f"OpenFoodFacts API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching product from OpenFoodFacts: {str(e)}")
            return None
    
    @async_cache_response(ttl=86400)  # Cache for 24 hours
    async def search_products(self, query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Search products by name"""
        try:
            params = {
                "search_terms": query,
                "page": page,
                "page_size": page_size,
                "json": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.BASE_URL}/search", params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OpenFoodFacts API error: {response.status_code} - {response.text}")
                    return {"products": []}
        except Exception as e:
            logger.error(f"Error searching products in OpenFoodFacts: {str(e)}")
            return {"products": []}

# Factory function to get the appropriate API client
def get_fitness_api(api_name: str) -> Union[ExerciseDBAPI, NutritionixAPI, WgerAPI, OpenFoodFactsAPI]:
    """Get the appropriate fitness API client based on name"""
    apis = {
        "exercisedb": ExerciseDBAPI(),
        "nutritionix": NutritionixAPI(),
        "wger": WgerAPI(),
        "openfoodfacts": OpenFoodFactsAPI()
    }
    
    if api_name.lower() not in apis:
        raise ValueError(f"Unknown API name: {api_name}. Available APIs: {', '.join(apis.keys())}")
    
    return apis[api_name.lower()]

# Mock implementation for development/testing without API keys
class MockFitnessAPI:
    """Mock implementation of fitness APIs for development and testing"""
    
    async def get_exercises_by_muscle(self, muscle: str) -> List[Dict[str, Any]]:
        """Mock getting exercises by muscle group"""
        exercises = [
            {
                "id": "0001",
                "name": "Barbell Bench Press",
                "muscle_group": "chest",
                "equipment": "barbell",
                "difficulty": "intermediate"
            },
            {
                "id": "0002",
                "name": "Push-ups",
                "muscle_group": "chest",
                "equipment": "bodyweight",
                "difficulty": "beginner"
            },
            {
                "id": "0003",
                "name": "Dumbbell Flyes",
                "muscle_group": "chest",
                "equipment": "dumbbell",
                "difficulty": "intermediate"
            }
        ]
        
        if muscle.lower() == "back":
            return [
                {
                    "id": "0004",
                    "name": "Pull-ups",
                    "muscle_group": "back",
                    "equipment": "bodyweight",
                    "difficulty": "intermediate"
                },
                {
                    "id": "0005",
                    "name": "Deadlift",
                    "muscle_group": "back",
                    "equipment": "barbell",
                    "difficulty": "advanced"
                },
                {
                    "id": "0006",
                    "name": "Seated Cable Rows",
                    "muscle_group": "back",
                    "equipment": "cable",
                    "difficulty": "beginner"
                }
            ]
        elif muscle.lower() == "legs":
            return [
                {
                    "id": "0007",
                    "name": "Barbell Squat",
                    "muscle_group": "legs",
                    "equipment": "barbell",
                    "difficulty": "intermediate"
                },
                {
                    "id": "0008",
                    "name": "Leg Press",
                    "muscle_group": "legs",
                    "equipment": "machine",
                    "difficulty": "beginner"
                },
                {
                    "id": "0009",
                    "name": "Romanian Deadlift",
                    "muscle_group": "legs",
                    "equipment": "barbell",
                    "difficulty": "intermediate"
                }
            ]
        
        # Default to chest exercises
        return exercises
    
    async def get_nutrition_info(self, query: str) -> List[NutritionInfo]:
        """Mock getting nutrition information"""
        if "chicken" in query.lower():
            return [
                NutritionInfo(
                    name="Grilled Chicken Breast",
                    calories=165,
                    protein=31,
                    carbs=0,
                    fat=3.6,
                    serving_size="100",
                    serving_unit="g"
                )
            ]
        elif "rice" in query.lower():
            return [
                NutritionInfo(
                    name="White Rice, cooked",
                    calories=130,
                    protein=2.7,
                    carbs=28.2,
                    fat=0.3,
                    serving_size="100",
                    serving_unit="g"
                )
            ]
        else:
            # Generic response
            return [
                NutritionInfo(
                    name=query,
                    calories=random.randint(100, 500),
                    protein=random.randint(5, 30),
                    carbs=random.randint(10, 50),
                    fat=random.randint(2, 20),
                    serving_size="100",
                    serving_unit="g"
                )
            ] 