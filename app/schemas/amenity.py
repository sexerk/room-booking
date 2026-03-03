from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class AmenityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    icon: Optional[str] = Field(None, max_length=50)


class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    icon: Optional[str] = Field(None, max_length=50)


class Amenity(AmenityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)