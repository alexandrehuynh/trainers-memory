"""
Tests for multi-tenant data isolation.

This module contains tests to verify that the multi-tenant isolation works correctly.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.auth_utils import create_access_token
from app.db.models import User, Client, Workout, Exercise
from app.db import get_async_db

@pytest.fixture
async def db_session():
    """Get a test database session."""
    from app.db.session import get_test_async_session
    
    async for session in get_test_async_session():
        yield session

@pytest.fixture
def app_client():
    """Get a test client for the FastAPI application."""
    return AsyncClient(app=app, base_url="http://test")

@pytest.fixture
async def test_users(db_session: AsyncSession):
    """Create test users for multi-tenant testing."""
    # Create two users
    user1 = User(
        id=uuid.uuid4(),
        name="Test User 1",
        email="user1@example.com",
        password="hashed_password1",  # In real tests, use get_password_hash
        is_admin=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    user2 = User(
        id=uuid.uuid4(),
        name="Test User 2",
        email="user2@example.com",
        password="hashed_password2",
        is_admin=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    admin_user = User(
        id=uuid.uuid4(),
        name="Admin User",
        email="admin@example.com",
        password="hashed_password_admin",
        is_admin=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db_session.add(user1)
    db_session.add(user2)
    db_session.add(admin_user)
    await db_session.commit()
    
    # Create access tokens
    user1_token = create_access_token({"sub": str(user1.id), "email": user1.email, "name": user1.name})
    user2_token = create_access_token({"sub": str(user2.id), "email": user2.email, "name": user2.name})
    admin_token = create_access_token({
        "sub": str(admin_user.id), 
        "email": admin_user.email, 
        "name": admin_user.name,
    })
    
    return {
        "user1": {
            "id": str(user1.id),
            "token": user1_token,
            "data": user1
        },
        "user2": {
            "id": str(user2.id),
            "token": user2_token,
            "data": user2
        },
        "admin": {
            "id": str(admin_user.id),
            "token": admin_token,
            "data": admin_user
        }
    }

@pytest.fixture
async def test_clients(db_session: AsyncSession, test_users: dict):
    """Create test clients for each user."""
    # Create clients for user1
    client1_user1 = Client(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_users["user1"]["id"]),
        name="Client 1 for User 1",
        email="client1_user1@example.com",
        created_at=datetime.utcnow()
    )
    
    client2_user1 = Client(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_users["user1"]["id"]),
        name="Client 2 for User 1",
        email="client2_user1@example.com",
        created_at=datetime.utcnow()
    )
    
    # Create clients for user2
    client1_user2 = Client(
        id=uuid.uuid4(),
        user_id=uuid.UUID(test_users["user2"]["id"]),
        name="Client 1 for User 2",
        email="client1_user2@example.com",
        created_at=datetime.utcnow()
    )
    
    db_session.add(client1_user1)
    db_session.add(client2_user1)
    db_session.add(client1_user2)
    await db_session.commit()
    
    return {
        "user1": [
            {"id": str(client1_user1.id), "data": client1_user1},
            {"id": str(client2_user1.id), "data": client2_user1}
        ],
        "user2": [
            {"id": str(client1_user2.id), "data": client1_user2}
        ]
    }

@pytest.fixture
async def test_workouts(db_session: AsyncSession, test_users: dict, test_clients: dict):
    """Create test workouts for each client."""
    # Create workout for user1's first client
    client1_user1_id = uuid.UUID(test_clients["user1"][0]["id"])
    user1_id = uuid.UUID(test_users["user1"]["id"])
    
    workout1_user1 = Workout(
        id=uuid.uuid4(),
        client_id=client1_user1_id,
        user_id=user1_id,
        date=datetime.utcnow(),
        type="Strength",
        duration=60,
        notes="Test workout for user 1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create workout for user2's client
    client1_user2_id = uuid.UUID(test_clients["user2"][0]["id"])
    user2_id = uuid.UUID(test_users["user2"]["id"])
    
    workout1_user2 = Workout(
        id=uuid.uuid4(),
        client_id=client1_user2_id,
        user_id=user2_id,
        date=datetime.utcnow(),
        type="Cardio",
        duration=30,
        notes="Test workout for user 2",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db_session.add(workout1_user1)
    db_session.add(workout1_user2)
    await db_session.commit()
    
    # Create exercises for the workouts
    exercise1_user1 = Exercise(
        id=uuid.uuid4(),
        workout_id=workout1_user1.id,
        user_id=user1_id,
        name="Squat",
        sets=3,
        reps=10,
        weight=100.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    exercise1_user2 = Exercise(
        id=uuid.uuid4(),
        workout_id=workout1_user2.id,
        user_id=user2_id,
        name="Running",
        sets=1,
        reps=1,
        weight=0.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db_session.add(exercise1_user1)
    db_session.add(exercise1_user2)
    await db_session.commit()
    
    return {
        "user1": [
            {"id": str(workout1_user1.id), "data": workout1_user1, "exercises": [exercise1_user1]}
        ],
        "user2": [
            {"id": str(workout1_user2.id), "data": workout1_user2, "exercises": [exercise1_user2]}
        ]
    }

@pytest.mark.asyncio
async def test_client_isolation(app_client: AsyncClient, test_users: dict, test_clients: dict):
    """
    Test that users can only access their own clients.
    """
    # User 1 should only see their own clients
    response1 = await app_client.get(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    assert response1.status_code == 200
    clients1 = response1.json()
    
    # User 1 should have 2 clients
    assert len(clients1) == 2
    client_ids1 = [client["id"] for client in clients1]
    assert test_clients["user1"][0]["id"] in client_ids1
    assert test_clients["user1"][1]["id"] in client_ids1
    assert test_clients["user2"][0]["id"] not in client_ids1
    
    # User 2 should only see their own clients
    response2 = await app_client.get(
        "/api/v1/clients/",
        headers={"Authorization": f"Bearer {test_users['user2']['token']}"}
    )
    assert response2.status_code == 200
    clients2 = response2.json()
    
    # User 2 should have 1 client
    assert len(clients2) == 1
    client_ids2 = [client["id"] for client in clients2]
    assert test_clients["user2"][0]["id"] in client_ids2
    assert test_clients["user1"][0]["id"] not in client_ids2
    assert test_clients["user1"][1]["id"] not in client_ids2

@pytest.mark.asyncio
async def test_client_access_control(app_client: AsyncClient, test_users: dict, test_clients: dict):
    """
    Test that users cannot access another user's clients directly.
    """
    # User 1 tries to access User 2's client
    user2_client_id = test_clients["user2"][0]["id"]
    response = await app_client.get(
        f"/api/v1/clients/{user2_client_id}",
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    
    # Should get 404, not 403 (to prevent enumeration)
    assert response.status_code == 404
    
    # User 2 tries to access User 1's client
    user1_client_id = test_clients["user1"][0]["id"]
    response = await app_client.get(
        f"/api/v1/clients/{user1_client_id}",
        headers={"Authorization": f"Bearer {test_users['user2']['token']}"}
    )
    
    # Should get 404
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_workout_isolation(app_client: AsyncClient, test_users: dict, test_workouts: dict):
    """
    Test that users can only access their own workouts.
    """
    # User 1 should only see their own workouts
    response1 = await app_client.get(
        "/api/v1/workouts/",
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    assert response1.status_code == 200
    workouts1 = response1.json()
    
    # User 1 should have 1 workout
    assert len(workouts1) == 1
    workout_ids1 = [workout["id"] for workout in workouts1]
    assert test_workouts["user1"][0]["id"] in workout_ids1
    assert test_workouts["user2"][0]["id"] not in workout_ids1
    
    # User 2 should only see their own workouts
    response2 = await app_client.get(
        "/api/v1/workouts/",
        headers={"Authorization": f"Bearer {test_users['user2']['token']}"}
    )
    assert response2.status_code == 200
    workouts2 = response2.json()
    
    # User 2 should have 1 workout
    assert len(workouts2) == 1
    workout_ids2 = [workout["id"] for workout in workouts2]
    assert test_workouts["user2"][0]["id"] in workout_ids2
    assert test_workouts["user1"][0]["id"] not in workout_ids2

@pytest.mark.asyncio
async def test_workout_access_control(app_client: AsyncClient, test_users: dict, test_workouts: dict):
    """
    Test that users cannot access another user's workouts directly.
    """
    # User 1 tries to access User 2's workout
    user2_workout_id = test_workouts["user2"][0]["id"]
    response = await app_client.get(
        f"/api/v1/workouts/{user2_workout_id}",
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    
    # Should get 404
    assert response.status_code == 404
    
    # User 2 tries to access User 1's workout
    user1_workout_id = test_workouts["user1"][0]["id"]
    response = await app_client.get(
        f"/api/v1/workouts/{user1_workout_id}",
        headers={"Authorization": f"Bearer {test_users['user2']['token']}"}
    )
    
    # Should get 404
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_client_with_correct_user(app_client: AsyncClient, test_users: dict, db_session: AsyncSession):
    """
    Test that when a user creates a client, it's associated with their user_id.
    """
    # User 1 creates a new client
    client_data = {
        "name": "New Test Client",
        "email": "newclient@example.com",
        "phone": "555-1234",
        "notes": "Test notes"
    }
    
    response = await app_client.post(
        "/api/v1/clients/",
        json=client_data,
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    
    assert response.status_code == 201
    new_client = response.json()
    
    # Check that the client was created in the database
    from sqlalchemy import select
    query = select(Client).where(Client.id == uuid.UUID(new_client["id"]))
    result = await db_session.execute(query)
    client_db = result.scalars().first()
    
    # Check that the client is associated with User 1
    assert client_db is not None
    assert str(client_db.user_id) == test_users["user1"]["id"]

@pytest.mark.asyncio
async def test_create_workout_with_correct_user(app_client: AsyncClient, test_users: dict, test_clients: dict, db_session: AsyncSession):
    """
    Test that when a user creates a workout, it's associated with their user_id.
    """
    # User 1 creates a new workout for their client
    client_id = test_clients["user1"][0]["id"]
    workout_data = {
        "client_id": client_id,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "type": "Test Workout",
        "duration": 45,
        "notes": "Test workout notes",
        "exercises": [
            {
                "name": "Test Exercise",
                "sets": 3,
                "reps": 12,
                "weight": 50.0,
                "notes": "Test exercise notes"
            }
        ]
    }
    
    response = await app_client.post(
        "/api/v1/workouts/",
        json=workout_data,
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    
    assert response.status_code == 201
    new_workout = response.json()
    
    # Check that the workout was created in the database with the correct user_id
    from sqlalchemy import select
    query = select(Workout).where(Workout.id == uuid.UUID(new_workout["id"]))
    result = await db_session.execute(query)
    workout_db = result.scalars().first()
    
    assert workout_db is not None
    assert str(workout_db.user_id) == test_users["user1"]["id"]
    
    # Check that the exercise was created with the correct user_id too
    query = select(Exercise).where(Exercise.workout_id == uuid.UUID(new_workout["id"]))
    result = await db_session.execute(query)
    exercise_db = result.scalars().first()
    
    assert exercise_db is not None
    assert str(exercise_db.user_id) == test_users["user1"]["id"]

@pytest.mark.asyncio
async def test_admin_access(app_client: AsyncClient, test_users: dict, test_clients: dict):
    """
    Test that admin users can access data from any user.
    """
    # Admin user should be able to access User 1's client
    user1_client_id = test_clients["user1"][0]["id"]
    
    # First, test that admin can access the client directly
    response1 = await app_client.get(
        f"/api/v1/clients/{user1_client_id}",
        headers={"Authorization": f"Bearer {test_users['admin']['token']}"}
    )
    
    assert response1.status_code == 200
    assert response1.json()["id"] == user1_client_id
    
    # Admin user should be able to access User 2's client
    user2_client_id = test_clients["user2"][0]["id"]
    
    response2 = await app_client.get(
        f"/api/v1/clients/{user2_client_id}",
        headers={"Authorization": f"Bearer {test_users['admin']['token']}"}
    )
    
    assert response2.status_code == 200
    assert response2.json()["id"] == user2_client_id

@pytest.mark.asyncio
async def test_update_data_isolation(app_client: AsyncClient, test_users: dict, test_clients: dict):
    """
    Test that users can only update their own data.
    """
    # User 1 tries to update their own client
    user1_client_id = test_clients["user1"][0]["id"]
    update_data = {
        "name": "Updated Client Name",
        "notes": "Updated notes"
    }
    
    response1 = await app_client.put(
        f"/api/v1/clients/{user1_client_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_users['user1']['token']}"}
    )
    
    assert response1.status_code == 200
    assert response1.json()["name"] == "Updated Client Name"
    
    # User 2 tries to update User 1's client
    response2 = await app_client.put(
        f"/api/v1/clients/{user1_client_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_users['user2']['token']}"}
    )
    
    # Should get 404
    assert response2.status_code == 404 