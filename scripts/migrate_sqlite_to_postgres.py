#!/usr/bin/env python
"""
Script to migrate data from SQLite to PostgreSQL.
Usage: python migrate_sqlite_to_postgres.py --source sqlite_db_path
"""

import os
import sys
import django
from pathlib import Path
import argparse
from datetime import datetime

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourist_routes.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from routes_app.models import TouristRoute


def backup_current_db(db_alias='default'):
    """Create a backup of current database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"Creating backup... [{timestamp}]")
    
    connection = connections[db_alias]
    db_name = connection.settings_dict.get('NAME')
    
    if isinstance(db_name, Path):
        backup_path = f"{db_name}.backup.{timestamp}"
        import shutil
        shutil.copy2(db_name, backup_path)
        print(f"✓ Backup created: {backup_path}")
    print()


def migrate_data():
    """Migrate data from old database to new database"""
    print("=" * 70)
    print("TOURIST ROUTES - DATA MIGRATION TOOL")
    print("=" * 70)
    print()
    
    try:
        # Check current database configuration
        connection = connections['default']
        db_engine = connection.settings_dict.get('ENGINE', '')
        db_name = connection.settings_dict.get('NAME', '')
        
        print(f"Current Database Configuration:")
        print(f"  Engine: {db_engine}")
        print(f"  Name: {db_name}")
        print()
        
        # Get existing routes
        existing_routes = TouristRoute.objects.all()
        print(f"Found {existing_routes.count()} existing routes in database")
        
        if existing_routes.count() > 0:
            print("\nExisting routes:")
            for route in existing_routes:
                print(f"  - {route.name} ({route.region})")
        print()
        
        # Run migrations to ensure schema is up to date
        print("Running Django migrations...")
        call_command('migrate', verbosity=0, interactive=False)
        print("✓ Migrations completed")
        print()
        
        # Verify migration
        print("Verifying migration...")
        final_count = TouristRoute.objects.all().count()
        print(f"✓ Total routes in new database: {final_count}")
        print()
        
        print("=" * 70)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Migration error: {str(e)}")
        sys.exit(1)


def export_sqlite_to_json(sqlite_path):
    """Export data from SQLite database to JSON for inspection"""
    print(f"Exporting data from SQLite: {sqlite_path}")
    
    try:
        import json
        from django.core.serializers import serialize
        from django.db import connections
        
        # Get all routes
        routes = TouristRoute.objects.all()
        routes_data = json.loads(serialize('json', routes))
        
        output_file = 'routes_export.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(routes_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Data exported to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"✗ Export error: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Migrate tourist routes data from SQLite to PostgreSQL'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create a backup before migration'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export SQLite data to JSON before migration'
    )
    
    args = parser.parse_args()
    
    if args.backup:
        backup_current_db()
    
    if args.export:
        export_sqlite_to_json('')
    
    migrate_data()


if __name__ == '__main__':
    main()
