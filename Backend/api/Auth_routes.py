from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from Backend.Utilities.database import db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    dob: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        print(f"📝 Registration attempt: {request.username}")

        if len(request.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        if not request.phone.isdigit() or len(request.phone) != 10:
            raise HTTPException(status_code=400, detail="Please enter a valid 10-digit phone number.")

        if db.get_user_by_username(request.username):
            raise HTTPException(status_code=400, detail="Username already exists. Please choose another.")

        if db.get_user_by_email(request.email):
            raise HTTPException(status_code=400, detail="Email already registered. Please use another email.")

        try:
            birth_date = datetime.strptime(request.dob, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 13:
                raise HTTPException(status_code=400, detail="You must be at least 13 years old to register.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

        success = db.create_user({
            'username': request.username,
            'email':    request.email,
            'phone':    request.phone,
            'dob':      request.dob,
            'password': request.password
        })

        if not success:
            raise HTTPException(status_code=400, detail="Username or email already exists.")

        return {
            "success":  True,
            "message":  "Registration successful! Redirecting to login...",
            "username": request.username
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
async def login(request: LoginRequest):
    try:
        print(f"🔑 Login attempt: {request.username}")

        user = db.get_user_by_username(request.username)

        if not user:
            raise HTTPException(status_code=401, detail="User not found. Please check your username or sign up.")

        if user['password'] != request.password:
            raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")

        print(f"✅ Login successful: {request.username}")

        return {
            "success":  True,
            "message":  "Login successful! Redirecting...",
            "username": request.username
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/users")
async def list_all_users():
    users = db.get_all_users()
    return {
        "success":     True,
        "total_users": len(users),
        "users":       users
    }


@router.get("/test")
async def test_auth():
    return {
        "message":  "Auth API is running!",
        "storage":  "MySQL Database",
        "endpoints": [
            "POST /api/auth/register",
            "POST /api/auth/login",
            "GET  /api/auth/users",
            "GET  /api/auth/test"
        ]
    }