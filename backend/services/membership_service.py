from sqlalchemy import select
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.user_tenant import UserTenant


# ----------------------------
# ADD MEMBER
# ----------------------------
async def add_member_service(db, tenant_id, target_user_id, role, added_by):

    # Normalize role
    role = role.capitalize()

    # Check permission
    admin = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == added_by,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if not admin:
        raise Exception("You are not a member of this tenant")  # ✅ FIX

    if admin.role not in ["Owner", "Admin"]:
        raise Exception("Not authorized")

    # Prevent duplicate membership
    existing = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == target_user_id,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if existing:
        raise Exception("User already a member")

    member = UserTenant(
        user_id=target_user_id,
        tenant_id=tenant_id,
        role=role
    )

    db.add(member)
    await db.commit()

    return member


# ----------------------------
# CHANGE ROLE
# ----------------------------
async def change_role_service(db, tenant_id, target_user_id, new_role, actor_id):

    new_role = new_role.capitalize()  # ✅ FIX

    # 🔍 Get actor
    actor = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == actor_id,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if not actor:
        raise Exception("You are not a member of this tenant")

    if actor.role != "Owner":
        raise Exception("Only owner can change roles")

    # 🔍 Get member
    member = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == target_user_id,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if not member:
        raise Exception("Target user is not a member of this tenant")

    if member.role == "Owner":
        raise Exception("Cannot change owner role")

    # ✅ Update role
    member.role = new_role
    await db.commit()

    return {"message": "Role updated"}


# ----------------------------
# REMOVE MEMBER
# ----------------------------
async def remove_member_service(db, tenant_id, target_user_id, actor_id):

    actor = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == actor_id,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if not actor:
        raise Exception("You are not a member of this tenant")  # ✅ FIX

    member = (await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == target_user_id,
            UserTenant.tenant_id == tenant_id
        )
    )).scalar_one_or_none()

    if not member:
        raise Exception("User is not a member of this tenant")  # ✅ FIX

    if actor.role == "Floor":
        raise Exception("Not allowed")

    if actor.role == "Admin" and member.role == "Admin":
        raise Exception("Admin cannot remove Admin")

    if actor.role != "Owner" and member.role == "Admin":
        raise Exception("Only owner can remove Admin")

    removed_user_id = member.user_id

    await db.delete(member)
    await db.commit()

    return {"message": "Member removed"}