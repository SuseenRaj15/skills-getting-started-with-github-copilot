from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirects_to_static():
    response = client.get("/")
    assert response.status_code == 200  # Permanent redirect handled by FastAPI static files
    assert response.url.path == "/static/index.html"

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    # Test structure of an activity
    activity = list(data.values())[0]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity

def test_signup_for_activity():
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # First signup attempt should succeed
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Second signup attempt should fail
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_nonexistent_activity():
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_unregister_from_activity():
    activity_name = "Programming Class"
    email = "test_unregister@mergington.edu"
    
    # First sign up the student
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    
    # Then unregister them
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify they're no longer in the participants list
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity_name]["participants"]

def test_unregister_not_registered():
    response = client.delete("/activities/Chess Club/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]

def test_signup_full_activity():
    # Find an activity and fill it up
    response = client.get("/activities")
    activities = response.json()
    test_activity = None
    
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            test_activity = (name, details)
            break
    
    assert test_activity is not None, "No suitable activity found for testing"
    
    activity_name, details = test_activity
    remaining_spots = details["max_participants"] - len(details["participants"])
    
    # Fill up the activity
    for i in range(remaining_spots):
        email = f"filler{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to sign up one more student
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"]