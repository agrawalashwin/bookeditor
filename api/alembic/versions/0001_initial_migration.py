"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2025-09-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create manuscripts table
    op.create_table('manuscripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create manuscript_versions table
    op.create_table('manuscript_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manuscript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_tag', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chunks table
    op.create_table('chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manuscript_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter', sa.Integer(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['manuscript_version_id'], ['manuscript_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chunk_embeddings table
    op.create_table('chunk_embeddings',
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(3072), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chunk_id')
    )
    
    # Create edit_sessions table
    op.create_table('edit_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manuscript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instruction', sa.Text(), nullable=False),
        sa.Column('target_range', postgresql.INT4RANGE(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create edit_options table
    op.create_table('edit_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edit_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('option_label', sa.String(), nullable=False),
        sa.Column('before_text', sa.Text(), nullable=False),
        sa.Column('after_text', sa.Text(), nullable=False),
        sa.Column('diff_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['edit_session_id'], ['edit_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create applied_edits table
    op.create_table('applied_edits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edit_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chosen_option_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('applied_by', sa.String(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('from_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['chosen_option_id'], ['edit_options.id'], ),
        sa.ForeignKeyConstraint(['edit_session_id'], ['edit_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_version_id'], ['manuscript_versions.id'], ),
        sa.ForeignKeyConstraint(['to_version_id'], ['manuscript_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create style_prefs table
    op.create_table('style_prefs',
        sa.Column('manuscript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('manuscript_id', 'key')
    )
    
    # Add foreign key constraint for current_version_id
    op.create_foreign_key(None, 'manuscripts', 'manuscript_versions', ['current_version_id'], ['id'])
    
    # Create index for vector similarity search
    op.execute('CREATE INDEX ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_table('style_prefs')
    op.drop_table('applied_edits')
    op.drop_table('edit_options')
    op.drop_table('edit_sessions')
    op.drop_table('chunk_embeddings')
    op.drop_table('chunks')
    op.drop_table('manuscript_versions')
    op.drop_table('manuscripts')
    op.execute('DROP EXTENSION IF EXISTS vector')
