import os
import sys
import django

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catalog.settings')

# Initialize Django
django.setup()

from django.core.management import call_command
from courses.models import Category, Course

def run_demo():
    print("=== Django Database Demo ===")
    
    # Run migrations programmatically
    print("\n[Step 1] Running database migrations...")
    call_command('makemigrations', 'courses', interactive=False)
    call_command('migrate', interactive=False)
    
    # Clean up existing data to start fresh
    Course.objects.all().delete()
    Category.objects.all().delete()
    
    # 1. Create a Category
    print("\n[Step 2] Creating a Category...")
    cs_category = Category.objects.create(name="Computer Science")
    print(f"Created Category: {cs_category}")
    
    # 2. Create a Course
    print("\n[Step 3] Creating a Course...")
    mds_course = Course.objects.create(
        title="Software Systems Modelling and Development",
        instructor="Horia Cheval",
        description="Introduction to software architecture, testing, and verification.",
        year=2026,
        semester="spring",
        category=cs_category
    )
    print(f"Created Course: {mds_course} (Instructor: {mds_course.instructor}, Sem: {mds_course.semester})")
    
    # List courses
    print("\nListing all courses in database:")
    for c in Course.objects.all():
        print(f"  - ID {c.id}: {c.title} by {c.instructor}")
        
    # 3. Modify (Update) the Course
    print("\n[Step 4] Modifying (Updating) the Course...")
    # Let's change the instructor and description
    course_to_edit = Course.objects.get(id=mds_course.id)
    course_to_edit.instructor = "Horia Cheval (Updated)"
    course_to_edit.description = "Updated description with more advanced topics."
    course_to_edit.save()
    
    # Fetch again to verify
    updated_course = Course.objects.get(id=mds_course.id)
    print(f"Updated Course: {updated_course} (New Instructor: {updated_course.instructor})")
    
    # 4. Delete the Course
    print("\n[Step 5] Deleting the Course...")
    course_to_delete = Course.objects.get(id=mds_course.id)
    course_to_delete.delete()
    print(f"Deleted course with ID {mds_course.id}.")
    
    # Verify deletion
    remaining_count = Course.objects.filter(id=mds_course.id).count()
    print(f"Remaining courses with ID {mds_course.id} in database: {remaining_count}")
    print("\n=============================")

if __name__ == "__main__":
    run_demo()
