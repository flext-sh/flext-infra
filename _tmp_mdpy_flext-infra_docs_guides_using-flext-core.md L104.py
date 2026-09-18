# from flext-infra/docs/guides/using-flext-core.md:104
from flext_core import u

logger = u.fetch_logger(__name__)
logger.info("user.created", user_id=42)
