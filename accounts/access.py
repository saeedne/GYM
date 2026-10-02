MODULES = {
    "dashboard": "داشبورد",
    "members": "اعضا",
    "membership": "عضویت و قراردادها",
    "attendance": "حضور و غیاب",
    "access": "کنترل ورود",
    "training": "مربیان و کلاس‌ها",
    "store": "فروشگاه",
    "cafe": "کافی‌شاپ",
    "workouts": "تمرین و ارزیابی",
    "finance": "مالی و صندوق",
    "crm": "CRM و پیگیری",
    "reports": "گزارش‌ها",
    "api": "یکپارچه‌سازی API",
    "mobile": "پرتال موبایل",
    "equipment": "تجهیزات",
    "users": "کاربران و نقش‌ها",
}

def role_permission_choices():
    choices = [("view_" + key, f"مشاهده: {label}") for key, label in MODULES.items()]
    choices += [("add_" + key, f"ثبت: {label}") for key, label in MODULES.items() if key not in ("dashboard", "reports", "mobile")]
    choices += [("change_" + key, f"ویرایش: {label}") for key, label in MODULES.items() if key not in ("dashboard", "reports", "mobile")]
    choices += [("delete_" + key, f"حذف: {label}") for key, label in MODULES.items() if key not in ("dashboard", "reports", "mobile")]
    return choices

ROLE_PERMISSION_CHOICES = role_permission_choices()

PATH_MODULES = {
    "/members/": "members", "/membership/": "membership", "/attendance/": "attendance",
    "/access/": "access", "/training/": "training", "/store/": "store", "/cafe/": "cafe",
    "/fitness/": "workouts", "/finance/": "finance", "/crm/": "crm", "/reports/": "reports",
    "/equipment/": "equipment", "/mobile/": "mobile",
    "/api/": "api",
}
