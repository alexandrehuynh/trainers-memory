import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import uuid
from datetime import datetime, timedelta

# Import our FastAPI app
from app.main import app
from app.auth import create_access_token

# Create test client
client = TestClient(app)

# Mock environment variables and Supabase integration
@pytest.fixture(autouse=True)
def mock_env():
    with patch.dict(os.environ, {
        "JWT_SECRET": "test_secret_key",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test_key",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASS": "test_pass",
    }):
        yield

# Mock authentication
@pytest.fixture
def auth_headers():
    # Create a mock JWT token
    user_data = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "user_metadata": {"role": "trainer"}
    }
    token = create_access_token(
        data=user_data,
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}

# Mock database session
@pytest.fixture
def mock_db_session():
    db_mock = MagicMock()
    with patch("app.db.get_async_db", return_value=db_mock):
        yield db_mock

# Tests for API endpoints
class TestClientEndpoints:
    
    @patch("app.routers.clients.AsyncClientRepository")
    def test_get_clients(self, mock_repo, auth_headers, mock_db_session):
        # Setup mock data
        mock_client = MagicMock()
        mock_client.id = uuid.uuid4()
        mock_client.name = "Test Client"
        mock_client.email = "test@example.com"
        mock_client.phone = "555-1234"
        mock_client.notes = "Test notes"
        mock_client.created_at = datetime.utcnow()
        mock_client.updated_at = datetime.utcnow()
        
        # Configure mock repository
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.get_all.return_value = [mock_client]
        
        # Make request
        response = client.get("/api/v1/clients", headers=auth_headers)
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert len(response.json()["data"]["clients"]) == 1
        assert response.json()["data"]["clients"][0]["name"] == "Test Client"

class TestWorkoutEndpoints:
    
    @patch("app.routers.workouts.AsyncWorkoutRepository")
    @patch("app.routers.workouts.AsyncClientRepository")
    @patch("app.routers.workouts.AsyncExerciseRepository")
    def test_get_workouts(self, mock_exercise_repo, mock_client_repo, mock_workout_repo, auth_headers, mock_db_session):
        # Setup mock workout
        mock_workout = MagicMock()
        mock_workout.id = uuid.uuid4()
        mock_workout.client_id = uuid.uuid4()
        mock_workout.date = datetime.utcnow()
        mock_workout.type = "Strength"
        mock_workout.duration = 60
        mock_workout.notes = "Test workout"
        mock_workout.created_at = datetime.utcnow()
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.name = "Test Client"
        
        # Setup mock exercise
        mock_exercise = MagicMock()
        mock_exercise.id = uuid.uuid4()
        mock_exercise.name = "Bench Press"
        mock_exercise.sets = 3
        mock_exercise.reps = 10
        mock_exercise.weight = 135.0
        mock_exercise.notes = "Test exercise"
        
        # Configure mock repositories
        mock_workout_repo_instance = mock_workout_repo.return_value
        mock_workout_repo_instance.get_all.return_value = [mock_workout]
        
        mock_client_repo_instance = mock_client_repo.return_value
        mock_client_repo_instance.get_by_id.return_value = mock_client
        
        mock_exercise_repo_instance = mock_exercise_repo.return_value
        mock_exercise_repo_instance.get_by_workout.return_value = [mock_exercise]
        
        # Make request
        response = client.get("/api/v1/workouts", headers=auth_headers)
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert len(response.json()["data"]["workouts"]) == 1
        assert response.json()["data"]["workouts"][0]["client_name"] == "Test Client"
        assert len(response.json()["data"]["workouts"][0]["exercises"]) == 1
        assert response.json()["data"]["workouts"][0]["exercises"][0]["name"] == "Bench Press"

# Run the tests with pytest -xvs 