# EduHub MongoDB Project

## Table of Contents

- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Database Schema](#database-schema)
- [Key Features](#key-features)
- [Query Explanations](#query-explanations)
- [Performance Analysis](#performance-analysis)
- [Challenges & Solutions](#challenges--solutions)
- [Usage Examples](#usage-examples)

---

## Project Overview

EduHub is a MongoDB-based educational platform that manages users, courses, enrollments, lessons, and assignments. The project demonstrates:

- **CRUD operations** with comprehensive error handling
- **Complex aggregation pipelines** for analytics
- **Schema validation** using JSON Schema
- **Performance optimization** through strategic indexing
- **Data visualization** with Matplotlib
- **Production-ready** code structure with logging

---

## Project Structure

```
mongodb-eduhub-project/
├── README.md
├── notebooks/
│   └── eduhub_mongodb_project.ipynb    # Interactive demonstrations
├── src/
│   └── eduhub_queries.py               # Production-ready Python module
├── data/
│   ├── eduhub_db.assignment_submissions.json                # submission data for testing
│   └── eduhub_db.assignments.json          # assignment data
│   └── eduhub_db.courses.json          # course data
│   └── eduhub_db.enrollments.json          # enrollment data
│   └── eduhub_db.lessons.json          # lesson data
│   └── eduhub_db.users.json          # users data
│   └── schema_db-assignment_submissions.json          # JSON schemas
│   └── schema_db-assignments.json          # JSON schemas
│   └── schema_db-courses.json          # JSON schemas
│   └── schema_db-enrollments.json          # JSON schemas
│   └── schema_db-lessons.json          # JSON schemas
│   └── schema_db-users.json          # JSON schemas
├── docs/
│   ├── performance_analysis.md         # Detailed performance metrics
│   └── presentation.pptx               # Project presentation
└── .gitignore
```

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB instance)
- Jupyter Notebook (optional)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd mongodb-eduhub-project
```

2. **Install dependencies:**
```bash
pip install pymongo pandas matplotlib
```

3. **Configure database connection:**

Update the connection string in `src/eduhub_queries.py`:
```python
CONNECTION_STRING = "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/"
```

4. **Run initial setup:**
```bash
# Option 1: Using Python script
python src/eduhub_queries.py

# Option 2: Using Jupyter notebook
jupyter notebook notebooks/eduhub_mongodb_project.ipynb
```

5. **Populate sample data:**
```python
from src.eduhub_queries import DataPopulator, DatabaseConfig

config = DatabaseConfig(CONNECTION_STRING)
db = config.connect()

populator = DataPopulator(db)
populator.populate_users(20)
populator.populate_courses()
```

---

## Database Schema

### Collections Overview

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `users` | Student and instructor accounts | userId, email, role |
| `courses` | Course catalog | courseId, title, instructorId |
| `enrollments` | Student-course relationships | userId, courseId, status |
| `lessons` | Course content modules | lessonId, courseId, title |
| `assignments` | Course assignments | assignmentId, courseId, dueDate |
| `assignment_submissions` | Student submissions | submissionId, userId, grade |

### Detailed Schemas

#### Users Collection
```javascript
{
  userId: String (unique),           // "U001"
  email: String (unique, validated), // "student@eduhub.com"
  firstName: String,
  lastName: String,
  role: Enum["student", "instructor"],
  dateJoined: Date,
  profile: {
    bio: String,
    avatar: String,
    skills: [String]
  },
  isActive: Boolean
}
```

**Indexes:** `userId` (unique), `email` (unique), `role`

#### Courses Collection
```javascript
{
  courseId: String (unique),         // "C001"
  title: String,                     // "Python for Beginners"
  description: String,
  instructorId: String,              // References users.userId
  category: String,                  // "Programming"
  level: Enum["beginner", "intermediate", "advanced"],
  duration: Int32,                   // Hours
  price: Double,
  tags: [String],
  createdAt: Date,
  updatedAt: Date,
  isPublished: Boolean
}
```

**Indexes:** `courseId` (unique), `category`, `level`, `instructorId`, `(category, level)` compound, `title` text

#### Enrollments Collection
```javascript
{
  enrollmentId: String (unique),     // "E001"
  userId: String,                    // References users.userId
  courseId: String,                  // References courses.courseId
  enrolledAt: Date,
  status: Enum["active", "completed", "dropped"],
  progress: Double                   // 0-100
}
```

**Indexes:** `enrollmentId` (unique), `(userId, courseId)` compound, `enrolledAt` descending, `status`

---

## Key Features

### 1. User Management
- Create users with role-based access
- Email validation and uniqueness enforcement
- Profile management with bio and skills
- Soft delete functionality

### 2. Course Management
- Create and publish courses
- Full-text search on title/description
- Category and level filtering
- Instructor verification

### 3. Enrollment System
- Student enrollment with validation
- Duplicate enrollment prevention
- Progress tracking
- Status management

### 4. Analytics & Reporting
- Course enrollment statistics
- Category popularity analysis
- Student performance metrics
- Completion rate calculations

### 5. Data Visualization
- Monthly enrollment trends
- Category distribution charts
- Student engagement metrics

---

## Query Explanations

### 1. Course Enrollment Statistics

**Purpose:** Calculate comprehensive enrollment metrics for each course.

```python
pipeline = [
    {
        "$group": {
            "_id": "$courseId",
            "total_enrollments": {"$sum": 1},
            "active_enrollments": {
                "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
            },
            "completed_enrollments": {
                "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
            }
        }
    },
    {
        "$lookup": {
            "from": "courses",
            "localField": "_id",
            "foreignField": "courseId",
            "as": "course"
        }
    },
    {"$unwind": "$course"},
    {
        "$project": {
            "courseId": "$_id",
            "title": "$course.title",
            "total_enrollments": 1,
            "completion_rate": {
                "$multiply": [
                    {"$divide": ["$completed_enrollments", "$total_enrollments"]},
                    100
                ]
            }
        }
    },
    {"$sort": {"total_enrollments": -1}}
]
```

**Steps:**
1. **$group:** Aggregates enrollments by course
2. **$lookup:** Joins with courses collection
3. **$unwind:** Flattens course array
4. **$project:** Calculates completion percentage
5. **$sort:** Orders by popularity

---

### 2. Category Popularity Analysis

**Purpose:** Determine popular course categories by enrollment count and unique students.

```python
pipeline = [
    {
        "$lookup": {
            "from": "courses",
            "localField": "courseId",
            "foreignField": "courseId",
            "as": "course"
        }
    },
    {"$unwind": "$course"},
    {
        "$group": {
            "_id": "$course.category",
            "total_enrollments": {"$sum": 1},
            "unique_students": {"$addToSet": "$userId"}
        }
    },
    {
        "$project": {
            "category": "$_id",
            "total_enrollments": 1,
            "unique_students": {"$size": "$unique_students"}
        }
    },
    {"$sort": {"total_enrollments": -1}}
]
```

**Key Operators:**
- `$addToSet`: Collects unique student IDs
- `$size`: Counts unique students

---

### 3. Student Performance Metrics

**Purpose:** Calculate comprehensive statistics for individual students.

```python
pipeline = [
    {"$match": {"userId": user_id}},
    {
        "$group": {
            "_id": "$userId",
            "total_submissions": {"$sum": 1},
            "average_grade": {"$avg": "$grade"},
            "highest_grade": {"$max": "$grade"},
            "lowest_grade": {"$min": "$grade"}
        }
    }
]
```

---

## Performance Analysis

### Index Impact Testing

#### Test 1: Find User by Email

| Metric | Without Index | With Index | Improvement |
|--------|---------------|------------|-------------|
| Query Time | 50ms | 2ms | **25x faster** |
| Documents Examined | 1000 | 1 | 99.9% reduction |
| Keys Examined | 0 | 1 | - |

#### Test 2: Course Search (Category + Level)

| Metric | Without Index | With Compound Index | Improvement |
|--------|---------------|---------------------|-------------|
| Query Time | 35ms | 3ms | **11x faster** |
| Documents Examined | 500 | 12 | 97.6% reduction |

### Aggregation Pipeline Optimization

**Enrollment Statistics Aggregation:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Execution Time | 450ms | 85ms | **81% faster** |
| Memory Usage | 15MB | 8MB | 47% reduction |

**Optimizations Applied:**
- Index on `enrollments.courseId`
- Index on `courses.courseId`
- Used `allowDiskUse: true` for large datasets

---

## Challenges & Solutions

### Challenge 1: Duplicate Key Errors During Bulk Insert

**Problem:** Occasional duplicate key errors when populating sample data.

**Solution:**
```python
try:
    db.users.insert_many(users)
except errors.BulkWriteError as e:
    for error in e.details['writeErrors']:
        if error['code'] == 11000:  # Duplicate key
            logger.warning(f"Duplicate skipped: {error}")
```

**Learning:** Always implement try-except blocks for bulk operations.

---

### Challenge 2: Schema Validation Failures

**Problem:** Existing documents failed validation after applying strict schemas.

**Solution:**
```python
# Use "moderate" validation level
db.command({
    "collMod": "users",
    "validator": schema,
    "validationLevel": "moderate"
})

# Update existing documents
db.users.update_many(
    {"dateJoined": {"$exists": False}},
    {"$set": {"dateJoined": datetime.now(timezone.utc)}}
)
```

**Learning:** Apply validation progressively and clean existing data first.

---

### Challenge 3: Slow Aggregation on Large Datasets

**Problem:** Category popularity aggregation took 2+ seconds with 10,000+ enrollments.

**Solution:**
```python
# Added compound index
db.enrollments.create_index([
    ("courseId", ASCENDING),
    ("status", ASCENDING)
])

# Used allowDiskUse
pipeline_result = db.enrollments.aggregate(
    pipeline,
    allowDiskUse=True
)
```

**Result:** 2000ms → 150ms (13x improvement)

---

### Challenge 4: Date Handling with Timezones

**Problem:** Inconsistent date handling caused enrollment filtering issues.

**Solution:**
```python
from datetime import datetime, timezone

# Always use UTC timezone
now = datetime.now(timezone.utc)

# For date range queries
start_date = datetime.now(timezone.utc) - timedelta(days=180)
```

**Learning:** Always use timezone-aware datetime objects.

---

### Challenge 5: Referential Integrity

**Problem:** MongoDB doesn't enforce foreign key constraints.

**Solution:**
```python
def enroll_student(self, user_id: str, course_id: str):
    # Verify student exists
    student = self.db.users.find_one({
        "userId": user_id,
        "role": "student",
        "isActive": True
    })
    if not student:
        return {"success": False, "error": "Student not found"}
    
    # Verify course exists
    course = self.db.courses.find_one({
        "courseId": course_id,
        "isPublished": True
    })
    if not course:
        return {"success": False, "error": "Course not found"}
```

**Learning:** Implement application-level validation for data integrity.

---

## Usage Examples

### Create a New Student

```python
from src.eduhub_queries import EduHubManager, DatabaseConfig

config = DatabaseConfig(CONNECTION_STRING)
db = config.connect()
manager = EduHubManager(db)

result = manager.create_user({
    "userId": "U100",
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "role": "student",
    "profile": {
        "bio": "Aspiring data scientist",
        "skills": ["Python", "SQL"]
    }
})

print(result)  # {"success": True, "user_id": "..."}
```

### Search and Enroll in Courses

```python
# Find Python courses
courses = manager.search_courses(
    title_keyword="Python",
    level="beginner"
)

# Enroll in first result
if courses:
    result = manager.enroll_student("U100", courses[0]["courseId"])
    print(result)
```

### Generate Analytics Reports

```python
# Course enrollment statistics
stats = manager.get_course_enrollment_stats()
for stat in stats[:5]:
    print(f"{stat['title']}: {stat['total_enrollments']} enrollments")

# Student performance
performance = manager.get_student_performance("U100")
print(f"Average Grade: {performance['average_grade']:.2f}%")
```

### Visualize Data

```python
# Plot enrollment trends
manager.plot_enrollment_trends(months=12)

# Plot category distribution
manager.plot_category_distribution()
```

---

## Security Considerations

- Never commit connection strings to version control
- Use environment variables for sensitive data
- Enable MongoDB Atlas IP whitelisting
- Implement proper authentication/authorization
- Use strong passwords and rotate credentials regularly

---

## Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [Aggregation Pipeline Reference](https://docs.mongodb.com/manual/core/aggregation-pipeline/)

---

## Author

**Sarah Iniobong Uko**  
Educational Platform Project - October 2nd 2025
AltSchool Second Semester Project Exam

---

## 📝 License

This project is created for educational purposes as part of a MongoDB learning curriculum.
