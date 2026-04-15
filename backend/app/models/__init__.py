"""
Import all ORM models here so Alembic's env.py only needs to import this
module to discover every table during `alembic revision --autogenerate`.
"""
from app.models.user import User  # noqa: F401
from app.models.classroom import Classroom, Enrollment  # noqa: F401
from app.models.assignment import Assignment, RubricCriteria  # noqa: F401
from app.models.submission import Submission  # noqa: F401
from app.models.feedback import AIFeedback  # noqa: F401
from app.models.grade import Grade  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.file_attachment import FileAttachment  # noqa: F401
from app.models.topic import Topic  # noqa: F401
from app.models.announcement import Announcement  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.criterion_grade import CriterionGrade  # noqa: F401
