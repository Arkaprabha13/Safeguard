from pydantic import BaseModel, EmailStr, Field, GetJsonSchemaHandler
from pydantic_core import core_schema
from typing import Optional, Literal, Any, Dict
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        source_type: Any, 
        handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x),
                return_schema=core_schema.str_schema(),
            )
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, 
        core_schema: core_schema.CoreSchema, 
        handler: GetJsonSchemaHandler
    ) -> Dict[str, Any]:
        return {
            "type": "string",
            "format": "objectid",
            "examples": ["507f1f77bcf86cd799439011", "64b7abdecf2160b649ab6085"]
        }

# User Models
class UserBase(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    middleName: Optional[str] = Field(None, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    firstName: Optional[str] = Field(None, min_length=1, max_length=50)
    lastName: Optional[str] = Field(None, min_length=1, max_length=50)
    middleName: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = None
    address: Optional[str] = None

class UserResponse(UserBase):
    id: PyObjectId = Field(alias="_id")
    safetyScore: Optional[int] = 85
    location: Optional[dict] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# Contact Models
class ContactBase(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    middleName: Optional[str] = Field(None, max_length=50)
    phone: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    relationship: str = Field(..., min_length=1)
    priority: Literal["high", "medium", "low"] = "medium"

class ContactCreate(ContactBase):
    userId: str = Field(..., min_length=1)

class ContactUpdate(BaseModel):
    firstName: Optional[str] = Field(None, min_length=1, max_length=50)
    lastName: Optional[str] = Field(None, min_length=1, max_length=50)
    middleName: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    relationship: Optional[str] = Field(None, min_length=1)
    priority: Optional[Literal["high", "medium", "low"]] = None

class ContactResponse(ContactBase):
    id: PyObjectId = Field(alias="_id")
    userId: str
    avatar: Optional[str] = None
    lastContact: Optional[datetime] = None
    isOnline: Optional[bool] = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# Activity Models
class ActivityBase(BaseModel):
    type: Literal["location_shared", "contact_called", "check_in", "emergency_alert"]
    description: str = Field(..., min_length=1)
    status: Literal["success", "pending", "failed"] = "success"
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ActivityCreate(ActivityBase):
    userId: str = Field(..., min_length=1)

class ActivityResponse(ActivityBase):
    id: PyObjectId = Field(alias="_id")
    userId: str
    createdAt: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Response Models for API Documentation
class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Error Models
class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
class ValidationErrorResponse(BaseModel):
    detail: str
    errors: Dict[str, Any]
    status_code: int = 422
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)