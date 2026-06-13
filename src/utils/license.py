"""Local license management with machine code binding.

Supports offline one-machine-one-code activation. The license key encodes
a machine fingerprint and an optional expiry timestamp, signed with HMAC-SHA256.
"""
import base64
import hashlib
import hmac
import json
import os
import platform
import struct
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


from .config import APP_NAME, TRIAL_DAYS

DEFAULT_SECRET = b"OfficeMeta2024KB"  # Change this for production


def _stable_machine_id() -> str:
    """Generate a stable cross-platform machine fingerprint.

    Tries multiple sources and combines them into a single hash. Not
    bullet-proof, but sufficient to stop casual license sharing.
    """
    parts = [
        platform.node() or "unknown",
        platform.machine() or "unknown",
        platform.processor() or "unknown",
        platform.system() or "unknown",
    ]

    system = platform.system()
    try:
        if system == "Windows":
            for cmd in [
                ["wmic", "csproduct", "get", "UUID", "/value"],
                ["wmic", "cpu", "get", "ProcessorId", "/value"],
                ["wmic", "bios", "get", "SerialNumber", "/value"],
            ]:
                try:
                    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=3).decode("utf-8", errors="ignore")
                    for line in out.splitlines():
                        if "=" in line:
                            parts.append(line.split("=", 1)[1].strip())
                except Exception:
                    continue
        elif system == "Darwin":
            try:
                out = subprocess.check_output(
                    ["system_profiler", "SPHardwareDataType"],
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                ).decode("utf-8", errors="ignore")
                for line in out.splitlines():
                    if "Hardware UUID" in line or "Serial Number" in line:
                        parts.append(line.split(":", 1)[1].strip())
            except Exception:
                pass
            for key in ["IOPlatformUUID", "IOPlatformSerialNumber"]:
                try:
                    out = subprocess.check_output(
                        ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                    ).decode("utf-8", errors="ignore")
                    for line in out.splitlines():
                        if key in line and '"' in line:
                            parts.append(line.split('"')[-2])
                except Exception:
                    continue
        else:  # Linux and others
            for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                try:
                    with open(path) as f:
                        parts.append(f.read().strip())
                except Exception:
                    continue
            try:
                out = subprocess.check_output(["dmidecode", "-s", "system-uuid"], stderr=subprocess.DEVNULL, timeout=3).decode("utf-8", errors="ignore")
                parts.append(out.strip())
            except Exception:
                pass
    except Exception:
        pass

    combined = "|".join(p for p in parts if p and p.lower() != "unknown" and p.lower() != "to be filled by o.e.m.")
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:32]


def _get_secret() -> bytes:
    env = os.environ.get("OME_LICENSE_SECRET", "")
    if env:
        return env.encode("utf-8")
    return DEFAULT_SECRET


def _encode_key(machine_hash: str, expiry_ts: int) -> str:
    """Encode machine hash + expiry + signature into a readable license key."""
    secret = _get_secret()
    random_part = os.urandom(2)
    # Payload: machine_hash(16 bytes hex) + expiry(4 bytes uint32) + random(2 bytes)
    machine_bytes = bytes.fromhex(machine_hash[:16].ljust(16, "0"))
    payload = machine_bytes + struct.pack(">I", expiry_ts) + random_part
    signature = hmac.new(secret, payload, hashlib.sha256).digest()[:16]
    full = payload + signature
    encoded = base64.b32encode(full).decode("ascii")
    return "-".join(encoded[i:i + 4] for i in range(0, len(encoded), 4))


def _decode_key(key: str) -> Optional[Dict[str, any]]:
    """Decode and validate a license key. Returns dict or None."""
    key = key.strip().upper().replace("-", "").replace(" ", "")
    if len(key) != 48:
        return None
    try:
        full = base64.b32decode(key)
    except Exception:
        return None
    if len(full) != 30:
        return None
    payload = full[:14]
    signature = full[14:]
    machine_bytes = payload[:8]
    expiry_ts = struct.unpack(">I", payload[8:12])[0]
    random_part = payload[12:14]

    secret = _get_secret()
    expected = hmac.new(secret, payload, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(signature, expected):
        return None

    return {
        "machine_hash": machine_bytes.hex(),
        "expiry_ts": expiry_ts,
        "random": random_part.hex(),
    }


def generate_license_key(machine_code: str, days: int = 0, secret: Optional[str] = None) -> str:
    """Generate a license key bound to a machine code.

    Args:
        machine_code: The user's machine code from get_machine_code().
        days: Number of days until expiry; 0 means perpetual.
        secret: Optional HMAC secret override.
    """
    old_secret = os.environ.get("OME_LICENSE_SECRET")
    if secret:
        os.environ["OME_LICENSE_SECRET"] = secret
    try:
        if days > 0:
            expiry_ts = int(time.time()) + days * 86400
        else:
            expiry_ts = 0
        return _encode_key(machine_code, expiry_ts)
    finally:
        if old_secret is None:
            os.environ.pop("OME_LICENSE_SECRET", None)
        else:
            os.environ["OME_LICENSE_SECRET"] = old_secret


def get_machine_code() -> str:
    """Return the machine code to show to users."""
    return _stable_machine_id()


def _license_store_path() -> Path:
    """Path to store trial/activation state."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    folder = base / APP_NAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "license.json"


def _load_store() -> Dict:
    path = _license_store_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_store(data: Dict) -> None:
    path = _license_store_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _record_trial_start() -> None:
    store = _load_store()
    if "trial_start" not in store:
        store["trial_start"] = int(time.time())
        _save_store(store)


def get_trial_days_left() -> int:
    """Return remaining trial days."""
    _record_trial_start()
    store = _load_store()
    start = store.get("trial_start", int(time.time()))
    elapsed = int(time.time()) - start
    remaining = TRIAL_DAYS * 86400 - elapsed
    return max(0, remaining // 86400)


def is_trial_active() -> bool:
    """Check if trial period is still active."""
    return get_trial_days_left() > 0


def validate_license(license_key: str) -> Dict[str, any]:
    """Validate a license key and return status dict."""
    decoded = _decode_key(license_key)
    if not decoded:
        return {"valid": False, "reason": "激活码无效或格式错误"}

    current_machine = _stable_machine_id()
    if decoded["machine_hash"] != current_machine[:16].ljust(16, "0"):
        return {"valid": False, "reason": "激活码与当前机器不匹配"}

    if decoded["expiry_ts"] > 0 and int(time.time()) > decoded["expiry_ts"]:
        return {"valid": False, "reason": "激活码已过期"}

    return {"valid": True, "reason": "激活有效"}


def get_license_status(license_key: Optional[str] = None) -> Dict[str, any]:
    """Return overall license status for the application."""
    store = _load_store()
    key = license_key or store.get("license_key", "")
    if key:
        result = validate_license(key)
        if result["valid"]:
            return {
                "active": True,
                "mode": "licensed",
                "message": "已激活",
                "days_left": None,
            }
        else:
            return {
                "active": False,
                "mode": "invalid",
                "message": result["reason"],
                "days_left": get_trial_days_left(),
            }

    days = get_trial_days_left()
    if days > 0:
        return {
            "active": True,
            "mode": "trial",
            "message": f"试用期剩余 {days} 天",
            "days_left": days,
        }
    return {
        "active": False,
        "mode": "expired",
        "message": "试用期已结束，请购买授权",
        "days_left": 0,
    }


def save_license_key(license_key: str) -> bool:
    """Save a license key locally after validation."""
    result = validate_license(license_key)
    if not result["valid"]:
        return False
    store = _load_store()
    store["license_key"] = license_key.strip()
    _save_store(store)
    return True


def clear_license() -> None:
    """Remove stored license key (mainly for testing)."""
    store = _load_store()
    store.pop("license_key", None)
    _save_store(store)
