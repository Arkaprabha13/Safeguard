from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from datetime import datetime

from ..models import ActivityCreate, ActivityResponse
from ..database import get_activities_collection
from .auth import get_current_user

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new safety activity"""
    collection = get_activities_collection()
    
    # Verify user can create activity for themselves
    if activity_data.userId != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create activity for another user"
        )
    
    # Create activity document
    activity_doc = activity_data.dict()
    activity_doc.update({
        "createdAt": datetime.utcnow()
    })
    
    # Insert activity
    result = await collection.insert_one(activity_doc)
    activity_doc["_id"] = result.inserted_id
    
    return ActivityResponse(**activity_doc)

@router.get("/user/{user_id}", response_model=List[ActivityResponse])
async def get_user_activities(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get all activities for a user"""
    collection = get_activities_collection()
    
    # Verify user can access activities
    if user_id != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's activities"
        )
    
    try:
        activities = await collection.find(
            {"userId": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(length=None)
        
        return [ActivityResponse(**activity) for activity in activities]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific activity by ID"""
    collection = get_activities_collection()
    
    try:
        activity = await collection.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Verify user owns this activity
        if activity["userId"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return ActivityResponse(**activity)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activity ID"
        )

@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an activity"""
    collection = get_activities_collection()
    
    try:
        # First check if activity exists and user owns it
        activity = await collection.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity["userId"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete activity
        result = await collection.delete_one({"_id": ObjectId(activity_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        return {"message": "Activity deleted successfully"}
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activity ID"
        )
