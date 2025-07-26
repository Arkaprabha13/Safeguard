from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from datetime import datetime

from ..models import ContactCreate, ContactResponse, ContactUpdate
from ..database import get_contacts_collection
from .auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new emergency contact"""
    collection = get_contacts_collection()
    
    # Verify user can create contact for themselves
    if contact_data.userId != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create contact for another user"
        )
    
    # Create contact document
    contact_doc = contact_data.dict()
    contact_doc.update({
        "avatar": None,
        "lastContact": None,
        "isOnline": False,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    })
    
    # Insert contact
    result = await collection.insert_one(contact_doc)
    contact_doc["_id"] = result.inserted_id
    
    return ContactResponse(**contact_doc)

@router.get("/user/{user_id}", response_model=List[ContactResponse])
async def get_user_contacts(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all contacts for a user"""
    collection = get_contacts_collection()
    
    # Verify user can access contacts
    if user_id != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's contacts"
        )
    
    try:
        contacts = await collection.find({"userId": user_id}).to_list(length=None)
        return [ContactResponse(**contact) for contact in contacts]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific contact by ID"""
    collection = get_contacts_collection()
    
    try:
        contact = await collection.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Verify user owns this contact
        if contact["userId"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return ContactResponse(**contact)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact ID"
        )

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a contact"""
    collection = get_contacts_collection()
    
    try:
        # First check if contact exists and user owns it
        contact = await collection.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        if contact["userId"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Prepare update data
        update_data = {k: v for k, v in contact_update.dict().items() if v is not None}
        if update_data:
            update_data["updatedAt"] = datetime.utcnow()
            
            # Update contact
            result = await collection.find_one_and_update(
                {"_id": ObjectId(contact_id)},
                {"$set": update_data},
                return_document=True
            )
            
            return ContactResponse(**result)
        
        return ContactResponse(**contact)
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact ID"
        )

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a contact"""
    collection = get_contacts_collection()
    
    try:
        # First check if contact exists and user owns it
        contact = await collection.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        if contact["userId"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete contact
        result = await collection.delete_one({"_id": ObjectId(contact_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        return {"message": "Contact deleted successfully"}
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact ID"
        )
