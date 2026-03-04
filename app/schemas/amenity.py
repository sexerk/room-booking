from pydantic import BaseModel, Field, ConfigDict


class AmenityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    icon: str | None = Field(None, max_length=50)


class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    icon: str | None = Field(None, max_length=50)


class Amenity(AmenityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)