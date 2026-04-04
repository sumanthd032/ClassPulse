"""Initial schema — all ClassPulse tables.

Revision ID: 0001
Revises:
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("role", sa.Enum("student", "teacher", "admin", name="userrole"), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── classrooms ────────────────────────────────────────────────────────────
    op.create_table(
        "classrooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("subject_code", sa.String(20), nullable=False),
        sa.Column("section", sa.String(10), nullable=False),
        sa.Column("semester", sa.String(10), nullable=False),
        sa.Column("join_code", sa.String(6), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("settings", postgresql.JSONB, nullable=False,
                  server_default='{"max_drafts":3,"late_policy":"penalty","ai_feedback":true}'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_classrooms_join_code", "classrooms", ["join_code"], unique=True)

    # ── enrollments ───────────────────────────────────────────────────────────
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classroom_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Enum("student", "co_teacher", name="enrollmentrole"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "classroom_id", name="uq_enrollment"),
    )
    op.create_index("ix_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("ix_enrollments_classroom_id", "enrollments", ["classroom_id"])

    # ── assignments ───────────────────────────────────────────────────────────
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("classroom_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_marks", sa.Integer, nullable=False),
        sa.Column("submission_type",
                  sa.Enum("text", "file", "both", name="submissiontype"), nullable=False),
        sa.Column("max_drafts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("late_policy",
                  sa.Enum("block", "penalty", "allow", name="latepolicy"), nullable=False),
        sa.Column("penalty_per_day", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_assignments_classroom_id", "assignments", ["classroom_id"])

    # ── rubric_criteria ───────────────────────────────────────────────────────
    op.create_table(
        "rubric_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("max_marks", sa.Integer, nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("levels", postgresql.JSONB, nullable=False,
                  server_default='{"excellent":"","good":"","average":"","poor":""}'),
    )
    op.create_index("ix_rubric_criteria_assignment_id", "rubric_criteria", ["assignment_id"])

    # ── submissions ───────────────────────────────────────────────────────────
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("file_url", sa.String(500), nullable=True),
        sa.Column("is_final", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("draft_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_late", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_submissions_assignment_student", "submissions",
                    ["assignment_id", "student_id"])
    # Partial unique index: only one final submission per student per assignment
    op.execute(
        "CREATE UNIQUE INDEX uq_final_submission ON submissions (assignment_id, student_id) "
        "WHERE is_final = true"
    )

    # ── ai_feedback ───────────────────────────────────────────────────────────
    op.create_table(
        "ai_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estimated_score", sa.Integer, nullable=False),
        sa.Column("feedback_text", sa.Text, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_feedback_submission_id", "ai_feedback", ["submission_id"])

    # ── grades ────────────────────────────────────────────────────────────────
    op.create_table(
        "grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("feedback", sa.Text, nullable=False, server_default=""),
        sa.Column("graded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_released", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_grades_submission_id", "grades", ["submission_id"])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum(
            "assignment_posted", "deadline_reminder", "grade_released", "feedback_ready",
            name="notificationtype"
        ), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("grades")
    op.drop_table("ai_feedback")
    op.drop_table("submissions")
    op.drop_table("rubric_criteria")
    op.drop_table("assignments")
    op.drop_table("enrollments")
    op.drop_table("classrooms")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS latepolicy")
    op.execute("DROP TYPE IF EXISTS submissiontype")
    op.execute("DROP TYPE IF EXISTS enrollmentrole")
    op.execute("DROP TYPE IF EXISTS userrole")
