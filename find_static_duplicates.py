from pathlib import Path
from collections import defaultdict

# Replace with your actual STATICFILES_DIRS
static_dirs = [
    Path("/srv/django/filesys/static"),
    Path("/srv/django/filesys/members/static"),
    Path("/srv/django/filesys/capture/static"),
]

# Dictionary to track seen paths and their sources
collected_files = defaultdict(list)

# Walk through each static directory
for base_dir in static_dirs:
    for path in base_dir.rglob("*"):
        if path.is_file():
            relative_path = path.relative_to(base_dir)
            collected_files[relative_path].append(str(path))

# Filter and print only duplicates
for rel_path, files in collected_files.items():
    if len(files) > 1:
        print(f"\nDuplicate: {rel_path}")
        for file_path in files:
            print(f" - {file_path}")
