"""
Menu Service
Handles menu item business logic and database queries.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate


class MenuService:

    @staticmethod
    async def list_menu_items(
        session: AsyncSession, is_active: Optional[bool] = None
    ) -> List[MenuItem]:
        """List menu items, optionally filtered by is_active."""
        stmt = select(MenuItem).order_by(MenuItem.name.asc())
        if is_active is not None:
            stmt = stmt.where(MenuItem.is_active == is_active)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, menu_item_id: int) -> MenuItem:
        """Retrieve a single menu item by ID with recipe mappings."""
        stmt = select(MenuItem).where(MenuItem.id == menu_item_id)
        result = await session.execute(stmt)
        menu_item = result.scalar_one_or_none()

        if not menu_item:
            raise NotFoundException("MenuItem", menu_item_id)
        return menu_item

    @staticmethod
    async def create_menu_item(session: AsyncSession, data: MenuItemCreate) -> MenuItem:
        """Create a new menu item, ensuring unique name."""
        name_check = select(MenuItem).where(MenuItem.name == data.name.strip())
        existing = (await session.execute(name_check)).scalar_one_or_none()
        if existing:
            raise ConflictException(
                f"A menu item with name '{data.name}' already exists."
            )

        menu_item = MenuItem(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            selling_price=data.selling_price,
            is_active=data.is_active,
        )
        session.add(menu_item)
        await session.commit()
        await session.refresh(menu_item)
        return menu_item

    @staticmethod
    async def update_menu_item(
        session: AsyncSession, menu_item_id: int, data: MenuItemUpdate
    ) -> MenuItem:
        """Update an existing menu item."""
        menu_item = await MenuService.get_by_id(session, menu_item_id)

        if data.name and data.name.strip() != menu_item.name:
            new_name = data.name.strip()
            name_check = select(MenuItem).where(MenuItem.name == new_name)
            existing = (await session.execute(name_check)).scalar_one_or_none()
            if existing and existing.id != menu_item_id:
                raise ConflictException(f"A menu item with name '{new_name}' already exists.")
            menu_item.name = new_name

        if data.description is not None:
            menu_item.description = data.description.strip() if data.description else None
        if data.selling_price is not None:
            menu_item.selling_price = data.selling_price
        if data.is_active is not None:
            menu_item.is_active = data.is_active

        await session.commit()
        await session.refresh(menu_item)
        return menu_item
