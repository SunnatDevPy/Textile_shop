"""Create admin user from .env configuration."""
import asyncio
import bcrypt
from models import db, AdminUser
from config import conf
from utils.logger import logger


async def create_admin_user():
    """Create admin user from environment variables."""

    logger.info("Creating admin user...")

    # Check if admin already exists
    from sqlalchemy import select
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == conf.ADMIN_USERNAME)
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        logger.info(f"Admin user '{conf.ADMIN_USERNAME}' already exists")
        logger.info(f"Admin ID: {existing_admin.id}")
        logger.info(f"Admin Status: {existing_admin.status}")
        logger.info(f"Admin Active: {existing_admin.is_active}")
        return existing_admin

    # Create new admin
    admin = AdminUser(
        username=conf.ADMIN_USERNAME,
        password=conf.ADMIN_PASS,  # Already hashed in .env
        status=AdminUser.StatusUser.ADMIN,
        is_active=True
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    logger.info("=" * 60)
    logger.info("Admin user created successfully!")
    logger.info("=" * 60)
    logger.info(f"Username: {admin.username}")
    logger.info(f"ID: {admin.id}")
    logger.info(f"Status: {admin.status}")
    logger.info(f"Active: {admin.is_active}")
    logger.info("=" * 60)

    return admin


async def main():
    """Main function."""
    try:
        await create_admin_user()
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise
    finally:
        await db.remove()


if __name__ == "__main__":
    asyncio.run(main())
