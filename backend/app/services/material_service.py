"""Material service."""
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.classroom import Enrollment, EnrollmentRole
from app.models.material import Material
from app.models.user import User
from app.schemas.material import MaterialCreate


async def _verify_teacher(db: AsyncSession, classroom_id: UUID, user_id: UUID, role: str) -> None:
    if role == "admin":
        return
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Only teachers can manage materials")


async def create_material(db: AsyncSession, classroom_id: UUID, data: MaterialCreate, current_user: User) -> Material:
    await _verify_teacher(db, classroom_id, current_user.id, current_user.role)
    mat = Material(
        classroom_id=classroom_id,
        topic_id=data.topic_id,
        title=data.title,
        material_type=data.material_type,
        url=data.url,
        description=data.description,
        file_id=data.file_id,
        created_by=current_user.id,
    )
    db.add(mat)
    await db.commit()
    await db.refresh(mat)
    return mat


async def list_materials(db: AsyncSession, classroom_id: UUID) -> List[Material]:
    result = await db.execute(
        select(Material)
        .where(Material.classroom_id == classroom_id)
        .order_by(Material.created_at.desc())
    )
    return result.scalars().all()


async def delete_material(db: AsyncSession, material_id: UUID, current_user: User) -> None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    mat = result.scalars().first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    await _verify_teacher(db, mat.classroom_id, current_user.id, current_user.role)
    await db.delete(mat)
    await db.commit()
