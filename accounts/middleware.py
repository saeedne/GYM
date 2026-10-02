from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from members.models import Member
from .access import PATH_MODULES

ADD_PAGE_VIEWS = {"member_create", "contract_create", "payment_create", "class_create", "class_book", "product_create", "sell", "entry_create", "lead_create", "create_equipment", "add_maintenance", "menu_item_create", "order_create"}
ADD_POST_VIEWS = {"member_create", "plan_list", "contract_create", "payment_create", "checkin", "credentials", "guests", "trainer_list", "class_create", "class_book", "menu_item_create", "order_create", "product_create", "sell", "entry_create", "account_list", "category_list", "lead_create", "lead_detail", "create_equipment", "add_maintenance", "plans", "plan_detail", "exercise_library", "assignments", "assessments"}
CHANGE_PAGE_VIEWS = {"member_edit", "plan_edit", "contract_edit", "policy", "credential_toggle", "checkout", "booking_cancel", "mark_attendance", "order_status", "stock_adjust", "user_edit", "user_access_edit", "role_edit", "trainer_edit", "class_edit", "product_edit", "menu_item_edit", "edit_equipment", "lead_edit", "exercise_edit", "account_edit", "category_edit"}
DELETE_VIEWS = {"member_delete", "user_membership_delete", "contract_delete", "plan_delete", "role_delete", "trainer_delete", "class_delete", "product_delete", "menu_item_delete", "lead_delete", "exercise_delete", "workout_plan_delete", "equipment_delete", "attendance_delete", "credential_delete", "guest_pass_delete", "account_delete", "category_delete"}

class ClubPermissionMiddleware(MiddlewareMixin):
    """Enforce role permissions inside the active club for staff web modules."""
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None
        path = request.path_info
        if path.startswith(("/admin/", "/static/", "/media/", "/login/", "/logout/", "/api/v1/")):
            return None
        module = "dashboard" if path == "/" else next((value for prefix, value in PATH_MODULES.items() if path.startswith(prefix)), None)
        if module is None:
            return None
        membership = getattr(request, "club_membership", None)
        if module == "mobile" and membership and membership.is_active and membership.webapp_enabled:
            return None
        if request.user.is_superuser:
            return None
        membership = getattr(request, "club_membership", None)
        if not membership or not membership.is_active:
            if membership and membership.is_active and membership.is_manager:
                return None
            raise PermissionDenied("برای این باشگاه نقشی با دسترسی لازم به حساب شما اختصاص داده نشده است.")
        if membership.is_manager:
            return None
        if membership.club_role_id and membership.club_role.club_id != membership.club_id:
            raise PermissionDenied("نقش انتخاب‌شده متعلق به باشگاه فعال نیست.")
        if membership.club_role_id and not membership.club_role.is_active:
            raise PermissionDenied("نقش دسترسی این حساب غیرفعال شده است.")
        method = request.method.upper()
        view_name = getattr(view_func, "__name__", "")
        if view_name in DELETE_VIEWS:
            action = "delete"
        elif method in ("GET", "HEAD"):
            action = "add" if view_name in ADD_PAGE_VIEWS else ("change" if view_name in CHANGE_PAGE_VIEWS else "view")
        elif method not in ("OPTIONS",):
            action = "add" if view_name in ADD_POST_VIEWS else "change"
        codename = f"{action}_{module}"
        allowed = membership.direct_permissions.filter(codename=codename, content_type__app_label="accounts").exists()
        if not allowed and membership.club_role_id and membership.club_role.is_active and membership.club_role.club_id == membership.club_id:
            allowed = membership.club_role.permissions.filter(codename=codename, content_type__app_label="accounts").exists()
        if not allowed:
            raise PermissionDenied("نقش شما اجازه‌ی انجام این عملیات را در باشگاه فعال نمی‌دهد.")
        return None
