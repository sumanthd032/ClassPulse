# Import all models here so Alembic's autogenerate can discover them.
# The order matters: models with FKs must come after the tables they reference.
from app.models.user import User, UserRole                          # noqa: F401
from app.models.classroom import Classroom, Enrollment, EnrollmentRole  # noqa: F401
from app.models.assignment import Assignment, RubricCriterion, SubmissionType, LatePolicy  # noqa: F401
from app.models.submission import Submission                        # noqa: F401
from app.models.ai_feedback import AIFeedback                       # noqa: F401
from app.models.grade import Grade                                  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
