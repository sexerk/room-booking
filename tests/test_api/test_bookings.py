from datetime import datetime, timedelta, timezone
from fastapi import status


def test_create_booking(client, test_user, test_room):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    start_time = datetime.now(timezone.utc) + timedelta(hours=2)
    end_time = start_time + timedelta(hours=1)

    response = client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": test_room.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "purpose": "Test meeting"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["room_id"] == test_room.id
    assert data["status"] == "pending"


def test_create_booking_conflict(client, test_user, test_room):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    start_time = datetime.now(timezone.utc) + timedelta(hours=3)
    end_time = start_time + timedelta(hours=2)

    response1 = client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": test_room.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "purpose": "First meeting"
        }
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": test_room.id,
            "start_time": (start_time + timedelta(minutes=30)).isoformat(),
            "end_time": (end_time - timedelta(minutes=30)).isoformat(),
            "purpose": "Second meeting"
        }
    )
    assert response2.status_code == status.HTTP_409_CONFLICT


def test_confirm_booking(client, test_user, test_room):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    start_time = datetime.now(timezone.utc) + timedelta(hours=4)
    end_time = start_time + timedelta(hours=1)

    create_response = client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": test_room.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )
    booking_id = create_response.json()["id"]

    confirm_response = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert confirm_response.status_code == status.HTTP_200_OK
    assert confirm_response.json()["status"] == "confirmed"


def test_cancel_booking(client, test_user, test_room):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    start_time = datetime.now(timezone.utc) + timedelta(hours=5)
    end_time = start_time + timedelta(hours=1)

    create_response = client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": test_room.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )
    booking_id = create_response.json()["id"]

    cancel_response = client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert cancel_response.status_code == status.HTTP_200_OK
    assert cancel_response.json()["status"] == "cancelled"