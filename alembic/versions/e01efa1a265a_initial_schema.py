"""Initial schema

Revision ID: e01efa1a265a
Revises: 
Create Date: 2025-11-18 16:39:23.382916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e01efa1a265a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('location_latitude', sa.REAL(), nullable=True),
        sa.Column('location_longitude', sa.REAL(), nullable=True),
        sa.Column('location_city', sa.Text(), nullable=True),
        sa.Column('location_region', sa.Text(), nullable=True),
        sa.Column('location_country', sa.Text(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create plants table
    op.create_table(
        'plants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('scientific_name', sa.Text(), nullable=False),
        sa.Column('plant_type', sa.Text(), nullable=False),
        sa.Column('season', sa.Text(), nullable=False),
        sa.Column('planting_method', sa.Text(), nullable=False),
        sa.Column('days_to_germination', sa.Integer(), nullable=False),
        sa.Column('days_to_maturity', sa.Integer(), nullable=False),
        sa.Column('spacing_inches', sa.Integer(), nullable=False),
        sa.Column('sun_requirements', sa.Text(), nullable=False),
        sa.Column('water_needs', sa.Text(), nullable=False),
        sa.Column('companion_plants', sa.Text(), nullable=False),
        sa.Column('avoid_plants', sa.Text(), nullable=False),
        sa.Column('climate_zones', sa.Text(), nullable=False),
        sa.Column('care_notes', sa.Text(), nullable=False),
        sa.Column('is_custom', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )

    # Create garden_plots table
    op.create_table(
        'garden_plots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )

    # Create planted_items table
    op.create_table(
        'planted_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=True),
        sa.Column('plot_id', sa.Integer(), nullable=True),
        sa.Column('x_position', sa.Integer(), nullable=True),
        sa.Column('y_position', sa.Integer(), nullable=True),
        sa.Column('planted_date', sa.DateTime(), nullable=True),
        sa.Column('expected_harvest', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id']),
        sa.ForeignKeyConstraint(['plot_id'], ['garden_plots.id'])
    )

    # Create care_tasks table
    op.create_table(
        'care_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('planted_item_id', sa.Integer(), nullable=True),
        sa.Column('task_type', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['planted_item_id'], ['planted_items.id'])
    )

    # Create indexes for performance optimization
    op.create_index('idx_plants_season', 'plants', ['season'])
    op.create_index('idx_plants_user_id', 'plants', ['user_id'])
    op.create_index('idx_garden_plots_user_id', 'garden_plots', ['user_id'])
    op.create_index('idx_planted_items_plot_id', 'planted_items', ['plot_id'])
    op.create_index('idx_care_tasks_planted_item_id', 'care_tasks', ['planted_item_id'])
    op.create_index('idx_care_tasks_due_date', 'care_tasks', ['due_date'])
    op.create_index('idx_care_tasks_due_date_completed', 'care_tasks', ['due_date', 'completed'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_care_tasks_due_date_completed', 'care_tasks')
    op.drop_index('idx_care_tasks_due_date', 'care_tasks')
    op.drop_index('idx_care_tasks_planted_item_id', 'care_tasks')
    op.drop_index('idx_planted_items_plot_id', 'planted_items')
    op.drop_index('idx_garden_plots_user_id', 'garden_plots')
    op.drop_index('idx_plants_user_id', 'plants')
    op.drop_index('idx_plants_season', 'plants')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('care_tasks')
    op.drop_table('planted_items')
    op.drop_table('garden_plots')
    op.drop_table('plants')
    op.drop_table('users')
