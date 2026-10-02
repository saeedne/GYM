import hashlib
from django.utils import timezone
from .models import ClubApiKey

def authenticate_api_request(request, required_scope):
    value=request.headers.get("Authorization", "")
    if not value.startswith("Bearer "): return None
    token=value[7:].strip()
    if "." not in token: return None
    prefix,secret=token.split(".",1)
    key=ClubApiKey.objects.select_related("club").filter(prefix=prefix,revoked_at__isnull=True).first()
    if not key or (key.expires_at and key.expires_at<=timezone.now()): return None
    if not hashlib.sha256(secret.encode()).hexdigest()==key.secret_hash: return None
    if required_scope not in key.scopes: return None
    ClubApiKey.objects.filter(pk=key.pk).update(last_used_at=timezone.now())
    return key
