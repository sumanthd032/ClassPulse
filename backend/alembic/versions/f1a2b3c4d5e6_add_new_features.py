"""add announcements topics materials comments files criterion_grades

Revision ID: f1a2b3c4d5e6
Revises: 98566dd7c071
Create Date: 2026-04-15 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '98566dd7c071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Fix notifications table (String PK → UUID) ----
    # Drop the old index on the String id first, then recreate the table properly
    op.drop_index('ix_notifications_id', table_name='notifications', if_exists=True)
    op.drop_index('ix_notifications_user_id', table_name='notifications', if_exists=True)
    op.drop_table('notifications')

    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)

    # ---- Add topic_id and scheduled_publish_at to assignments ----
    op.add_column('assignments', sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assignments', sa.Column('scheduled_publish_at', sa.DateTime(timezone=True), nullable=True))

    # ---- New tables ----

    # file_attachments (no FKs to other new tables)
    op.create_table(
        'file_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # topics
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_topics_classroom_id', 'topics', ['classroom_id'], unique=False)

    # Add FK from assignments to topics (after topics table exists)
    op.create_foreign_key('fk_assignments_topic_id', 'assignments', 'topics', ['topic_id'], ['id'], ondelete='SET NULL')

    # announcements
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('attachment_urls', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_announcements_classroom_id', 'announcements', ['classroom_id'], unique=False)

    # materials
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('material_type', sa.String(length=20), nullable=False, server_default='link'),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['file_id'], ['file_attachments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_materials_classroom_id', 'materials', ['classroom_id'], unique=False)

    # comments (references announcements and assignments)
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('announcement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # criterion_grades
    op.create_table(
        'criterion_grades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('grade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('criterion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['criterion_id'], ['rubric_criteria.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['grade_id'], ['grades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_criterion_grades_grade_id', 'criterion_grades', ['grade_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_criterion_grades_grade_id', table_name='criterion_grades')
    op.drop_table('criterion_grades')
    op.drop_table('comments')
    op.drop_index('ix_materials_classroom_id', table_name='materials')
    op.drop_table('materials')
    op.drop_index('ix_announcements_classroom_id', table_name='announcements')
    op.drop_table('announcements')
    op.drop_constraint('fk_assignments_topic_id', 'assignments', type_='foreignkey')
    op.drop_index('ix_topics_classroom_id', table_name='topics')
    op.drop_table('topics')
    op.drop_table('file_attachments')
    op.drop_column('assignments', 'scheduled_publish_at')
    op.drop_column('assignments', 'topic_id')

    # Restore old notifications table
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
