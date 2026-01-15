from django.conf import settings
from pywebpush import webpush, WebPushException
import logging

logger = logging.getLogger(__name__)

def send_web_push(subscription_info: dict, payload: dict) -> bool:
    """Send a Web Push notification using a subscription object.

    subscription_info should contain `endpoint`, `keys` with `p256dh` and `auth`.
    payload is a dict that will be JSON-encoded by pywebpush.
    """
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    vapid_contact = getattr(settings, 'WEB_PUSH_CONTACT', '')

    if not vapid_private or not vapid_public:
        logger.warning('VAPID keys not configured; skipping web push send')
        return False

    try:
        webpush(
            subscription_info=subscription_info,
            data=json_dumps(payload),
            vapid_private_key=vapid_private,
            vapid_claims={"sub": vapid_contact}
        )
        return True
    except WebPushException as exc:
        logger.exception('WebPush failed: %s', exc)
        return False


def json_dumps(payload):
    # Lazy import to avoid heavy JSON changes at module import time
    import json
    try:
        return json.dumps(payload)
    except Exception:
        return json.dumps({'text': str(payload)})
