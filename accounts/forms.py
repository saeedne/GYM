from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from core.models import Branch
from members.models import Member
from trainers.models import Trainer
from .access import ROLE_PERMISSION_CHOICES
from .models import ClubMembership, ClubRole, User

class ClubRoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple, label="سطح دسترسی",
    )
    class Meta:
        model = ClubRole
        fields = ["name", "description", "permissions", "is_active"]
    def __init__(self, *args, club, **kwargs):
        super().__init__(*args, **kwargs)
        content_type = ContentType.objects.get_for_model(ClubRole)
        allowed = {code for code, _ in ROLE_PERMISSION_CHOICES}
        self.fields["permissions"].queryset = Permission.objects.filter(content_type=content_type, codename__in=allowed).order_by("codename")
        self.fields["permissions"].label_from_instance = lambda p: dict(ROLE_PERMISSION_CHOICES).get(p.codename, p.name)
        self.club = club
    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicates = ClubRole.objects.filter(club=self.club, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError("این نام نقش در باشگاه فعال قبلاً تعریف شده است.")
        return name
    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit:
            obj.save()
            self.save_m2m()
        return obj

class ClubUserCreateForm(forms.Form):
    username = forms.CharField(label="نام کاربری", max_length=150)
    display_name = forms.CharField(label="نام و نام خانوادگی", max_length=120)
    email = forms.EmailField(label="ایمیل", required=False)
    password1 = forms.CharField(label="گذرواژه", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار گذرواژه", widget=forms.PasswordInput)
    club_role = forms.ModelChoiceField(label="نقش", queryset=ClubRole.objects.none(), required=False)
    branch = forms.ModelChoiceField(label="شعبه", queryset=Branch.objects.none(), required=False)
    member = forms.ModelChoiceField(label="پرونده عضو (اختیاری)", queryset=Member.objects.none(), required=False)
    trainer = forms.ModelChoiceField(label="پرونده مربی (اختیاری)", queryset=Trainer.objects.none(), required=False)
    is_manager = forms.BooleanField(label="مدیر این باشگاه", required=False)
    def __init__(self, *args, club, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        self.fields["club_role"].queryset = ClubRole.objects.filter(club=club, is_active=True)
        self.fields["branch"].queryset = Branch.objects.filter(club=club, is_active=True)
        self.fields["member"].queryset = Member.objects.filter(club=club, user__isnull=True)
        self.fields["trainer"].queryset = Trainer.objects.filter(club=club, user__isnull=True)
    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username
    def clean(self):
        data = super().clean()
        if data.get("password1") and data.get("password2"):
            if data["password1"] != data["password2"]:
                self.add_error("password2", "گذرواژه‌ها یکسان نیستند.")
            else:
                candidate = User(username=data.get("username", ""), display_name=data.get("display_name", ""), email=data.get("email", ""))
                try: password_validation.validate_password(data["password1"], user=candidate)
                except ValidationError as exc: self.add_error("password1", exc)
        if not data.get("is_manager") and not data.get("club_role") and not data.get("member") and not data.get("trainer"):
            self.add_error("club_role", "برای کاربر عادی یک نقش انتخاب کن.")
        return data
    def save(self):
        user = User(username=self.cleaned_data["username"], display_name=self.cleaned_data["display_name"], email=self.cleaned_data["email"])
        user.set_password(self.cleaned_data["password1"])
        user.save()
        role = self.cleaned_data.get("club_role")
        membership = ClubMembership.objects.create(
            user=user, club=self.club, branch=self.cleaned_data.get("branch"),
            role=role.name if role else ("مدیر باشگاه" if self.cleaned_data["is_manager"] else ("عضو" if self.cleaned_data.get("member") else "")),
            club_role=role, is_manager=self.cleaned_data["is_manager"], is_active=True,
        )
        member = self.cleaned_data.get("member")
        if member:
            member.user = user
            member.save(update_fields=["user"])
        trainer = self.cleaned_data.get("trainer")
        if trainer:
            trainer.user = user
            trainer.save(update_fields=["user"])
        return user

class ClubUserAssignmentForm(forms.ModelForm):
    member_profile = forms.ModelChoiceField(label="پرونده عضو", queryset=Member.objects.none(), required=False)
    trainer_profile = forms.ModelChoiceField(label="پرونده مربی", queryset=Trainer.objects.none(), required=False)
    direct_permissions = forms.ModelMultipleChoiceField(label="دسترسی‌های اختصاصی این کاربر", queryset=Permission.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = ClubMembership
        fields = ["branch", "club_role", "direct_permissions", "member_profile", "trainer_profile", "webapp_enabled", "is_manager", "is_active"]
    def __init__(self, *args, club, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        self.fields["branch"].queryset = Branch.objects.filter(club=club, is_active=True)
        self.fields["club_role"].queryset = ClubRole.objects.filter(club=club, is_active=True)
        content_type = ContentType.objects.get_for_model(ClubRole)
        allowed = {code for code, _ in ROLE_PERMISSION_CHOICES}
        self.fields["direct_permissions"].queryset = Permission.objects.filter(content_type=content_type, codename__in=allowed).order_by("codename")
        self.fields["direct_permissions"].label_from_instance = lambda p: dict(ROLE_PERMISSION_CHOICES).get(p.codename, p.name)
        self.fields["direct_permissions"].help_text = "این مجوزها فقط برای همین کاربر هستند و به مجوزهای نقش انتخاب‌شده اضافه می‌شوند. برای تعیین مستقل دسترسی، نقش را خالی بگذارید."
        self.fields["webapp_enabled"].help_text = "برای حساب‌های جدید به‌طور پیش‌فرض روشن است. با روشن بودن، کاربر می‌تواند وارد صفحه وب‌اپ شود؛ صفحه‌های داخلی طبق دسترسی‌های بالا کنترل می‌شوند."
        self.fields["member_profile"].queryset = Member.objects.filter(club=club).filter(Q(user__isnull=True) | Q(user_id=instance.user_id))
        self.fields["trainer_profile"].queryset = Trainer.objects.filter(club=club).filter(Q(user__isnull=True) | Q(user_id=instance.user_id))
        if not self.is_bound:
            self.initial["member_profile"] = Member.objects.filter(club=club, user_id=instance.user_id).first()
            self.initial["trainer_profile"] = Trainer.objects.filter(club=club, user_id=instance.user_id).first()
    def clean(self):
        data = super().clean()
        role = data.get("club_role")
        if role and role.club_id != self.instance.club_id:
            raise ValidationError("نقش باید متعلق به همین باشگاه باشد.")
        return data

class ClubUserProfileForm(forms.Form):
    username = forms.CharField(label="نام کاربری", max_length=150)
    display_name = forms.CharField(label="نام و نام خانوادگی", max_length=120, required=False)
    email = forms.EmailField(label="ایمیل", required=False)
    password1 = forms.CharField(label="گذرواژه جدید", required=False, widget=forms.PasswordInput(render_value=True))
    password2 = forms.CharField(label="تکرار گذرواژه جدید", required=False, widget=forms.PasswordInput(render_value=True))
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.is_bound:
            self.initial.update(username=user.username, display_name=user.display_name, email=user.email)
    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username
    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "گذرواژه‌ها یکسان نیستند.")
            elif p1:
                try: password_validation.validate_password(p1, user=self.user)
                except ValidationError as exc: self.add_error("password1", exc)
        return data
    def save(self):
        self.user.username = self.cleaned_data["username"]
        self.user.display_name = self.cleaned_data["display_name"]
        self.user.email = self.cleaned_data["email"]
        if self.cleaned_data.get("password1"):
            self.user.set_password(self.cleaned_data["password1"])
        self.user.save()
        return self.user
