
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import csv
import os
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

USERS_CSV = "Data/Assets/users.csv"

# Ensure Data directory exists
os.makedirs("Data", exist_ok=True)
os.makedirs("Data/Assets", exist_ok=True)

# Initialize CSV if it doesn't exist
if not os.path.exists(USERS_CSV):
    with open(USERS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'email', 'phone', 'dob', 'password', 'created_at'])
    print(f"✅ Created new users.csv at {USERS_CSV}")


# ========== REQUEST/RESPONSE MODELS ==========

class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    dob: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None


# ========== HELPER FUNCTIONS ==========

def get_all_users():
    """Read all users from CSV"""
    users = []
    try:
        with open(USERS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            users = list(reader)
    except FileNotFoundError:
        return []
    return users

def find_user_by_username(username: str):
    """Find user by username (case-insensitive)"""
    users = get_all_users()
    for user in users:
        if user['username'].lower() == username.lower():
            return user
    return None

def find_user_by_email(email: str):
    """Find user by email (case-insensitive)"""
    users = get_all_users()
    for user in users:
        if user['email'].lower() == email.lower():
            return user
    return None

def save_user_to_csv(user_data: dict):
    """Append new user to CSV"""
    with open(USERS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            user_data['username'],
            user_data['email'],
            user_data['phone'],
            user_data['dob'],
            user_data['password'],
            user_data['created_at']
        ])
    print(f"✅ User '{user_data['username']}' saved to CSV")


# ========== API ENDPOINTS ==========

@router.post("/register")
async def register(request: RegisterRequest):
    """
    Register new user - saves to CSV
    
    Matches your frontend registerForm validation
    """
    try:
        print(f"📝 Registration attempt: {request.username}")
        
        # Validation - Username length
        if len(request.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        
        # Validation - Password length
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Validation - Phone (10 digits)
        if not request.phone.isdigit() or len(request.phone) != 10:
            raise HTTPException(status_code=400, detail="Please enter a valid 10-digit phone number.")
        
        # Check username uniqueness
        if find_user_by_username(request.username):
            raise HTTPException(status_code=400, detail="Username already exists. Please choose another.")
        
        # Check email uniqueness
        if find_user_by_email(request.email):
            raise HTTPException(status_code=400, detail="Email already registered. Please use another email.")
        
        # Validate age (at least 13)
        try:
            birth_date = datetime.strptime(request.dob, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                raise HTTPException(status_code=400, detail="You must be at least 13 years old to register.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Create and save user
        user_data = {
            'username': request.username,
            'email': request.email,
            'phone': request.phone,
            'dob': request.dob,
            'password': request.password,  # Plaintext for demo - hash in production
            'created_at': datetime.now().isoformat()
        }
        
        save_user_to_csv(user_data)
        
        return {
            "success": True,
            "message": "Registration successful! Redirecting to login...",
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
        
        # Find user
        user = find_user_by_username(request.username)
        
        if not user:
            raise HTTPException(
                status_code=401, 
                detail="User not found. Please check your username or sign up."
            )
        
        # Verify password (plaintext comparison)
        if user['password'] != request.password:
            raise HTTPException(
                status_code=401, 
                detail="Incorrect password. Please try again."
            )
        
        print(f"✅ Login successful: {request.username}")
        
        return {
            "success": True,
            "message": "Login successful! Redirecting...",
            "username": request.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/users")
async def list_all_users():
    users = get_all_users()
    
    # Remove passwords for safety
    safe_users = []
    for user in users:
        safe_user = {k: v for k, v in user.items() if k != 'password'}
        safe_users.append(safe_user)
    
    return {
        "success": True,
        "total_users": len(safe_users),
        "users": safe_users
    }


@router.get("/test")
async def test_auth():
    """Test if auth routes are working"""
    return {
        "message": "Auth API is running!",
        "csv_location": USERS_CSV,
        "csv_exists": os.path.exists(USERS_CSV),
        "endpoints": [
            "POST /api/auth/register",
            "POST /api/auth/login",
            "GET /api/auth/users (debug only)",
            "GET /api/auth/test"
        ]
    }