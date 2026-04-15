"""Material routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialResponse
from app.services import material_service

router = APIRouter(tags=["Materials"])


@router.post(
    "/classrooms/{classroom_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_material(
    classroom_id: UUID,
    data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await material_service.create_material(db, classroom_id, data, current_user)


@router.get("/classrooms/{classroom_id}/materials", response_model=List[MaterialResponse])
async def list_materials(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await material_service.list_materials(db, classroom_id)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await material_service.delete_material(db, material_id, current_user)
