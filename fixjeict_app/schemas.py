from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None


class UserCreate(UserBase):
    role: str = "client"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    order: int = 0


class CategoryUpdate(CategoryBase):
    order: Optional[int] = None
    is_active: Optional[bool] = None


class Category(CategoryBase):
    id: int
    order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Ticket schemas
class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    priority: str = "normaal"


class TicketCreate(TicketBase):
    category_id: Optional[int] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category_id: Optional[int] = None
    fixer_id: Optional[int] = None
    estimated_hours: Optional[float] = None


class Ticket(TicketBase):
    id: int
    status: str
    client_id: int
    category_id: Optional[int] = None
    fixer_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: float
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    # Nested relations
    client: Optional[User] = None
    fixer: Optional[User] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    is_internal: bool = False


class Message(MessageBase):
    id: int
    ticket_id: int
    user_id: int
    is_internal: bool
    created_at: datetime
    user: Optional[User] = None

    class Config:
        from_attributes = True


# TicketNote schemas
class TicketNoteBase(BaseModel):
    content: str


class TicketNoteCreate(TicketNoteBase):
    pass


class TicketNote(TicketNoteBase):
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    user: Optional[User] = None

    class Config:
        from_attributes = True


# TimeLog schemas
class TimeLogBase(BaseModel):
    hours: int = 0
    minutes: int = 0
    description: Optional[str] = None


class TimeLogCreate(TimeLogBase):
    pass


class TimeLog(TimeLogBase):
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    total_hours: float
    user: Optional[User] = None

    class Config:
        from_attributes = True


# BlogPost schemas
class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None


class BlogPostCreate(BlogPostBase):
    is_published: bool = False


class BlogPostUpdate(BlogPostBase):
    is_published: Optional[bool] = None


class BlogPost(BlogPostBase):
    id: int
    slug: str
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# KnowledgeBase schemas
class KnowledgeBaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    category: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    is_published: bool = False


class KnowledgeBaseUpdate(KnowledgeBaseBase):
    is_published: Optional[bool] = None


class KnowledgeBase(KnowledgeBaseBase):
    id: int
    slug: str
    views: int
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lead schemas
class LeadBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    status: Optional[str] = None


class Lead(LeadBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Testimonial schemas
class TestimonialBase(BaseModel):
    name: str
    company: Optional[str] = None
    content: str
    rating: int = Field(default=5, ge=1, le=5)


class TestimonialCreate(TestimonialBase):
    is_published: bool = False


class TestimonialUpdate(TestimonialBase):
    is_published: Optional[bool] = None


class Testimonial(TestimonialBase):
    id: int
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True


# SiteConfig schemas
class SiteConfigBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SiteConfigCreate(SiteConfigBase):
    pass


class SiteConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class SiteConfig(SiteConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr


class TokenVerify(BaseModel):
    token: str


# Response schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    message: str
    success: bool = False
