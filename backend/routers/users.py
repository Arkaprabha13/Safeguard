from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from datetime import datetime

from ..models import UserResponse, UserUpdate
from ..database import get_users_collection
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile"""
    collection = get_users_collection()
    
    # Prepare update data
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if update_data:
        update_data["updatedAt"] = datetime.utcnow()
        
        # Update user
        result = await collection.find_one_and_update(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**result)
    
    return UserResponse(**current_user)

@router.delete("/me")
async def delete_current_user(current_user: dict = Depends(get_current_user)):
    """Delete current user account"""
    collection = get_users_collection()
    
    result = await collection.delete_one({"_id": ObjectId(current_user["_id"])})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User account deleted successfully"}

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID (admin or self only)"""
    collection = get_users_collection()
    
    # Only allow access to own profile for now
    if str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        user = await collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
