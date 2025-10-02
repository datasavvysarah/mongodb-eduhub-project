"""
EduHub MongoDB Project
A comprehensive educational platform management system using MongoDB and PyMongo.

Author: Sarah Iniobong Uko
Date: 2025
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, errors
from pymongo.collection import Collection
from pymongo.database import Database
import matplotlib.pyplot as plt
import pandas as pd
from bson import ObjectId, Int32

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eduhub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
    
    def connect(self, db_name: str = "eduhub_db") -> Database:
        """Establish database connection with connection pooling."""
        try:
            self.client = MongoClient(
                self.connection_string,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            logger.info(f"Successfully connected to database: {db_name}")
            return self.db
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")


class SchemaValidator:
    """Handles schema validation for MongoDB collections."""
    
    @staticmethod
    def get_user_schema() -> Dict:
        """Returns JSON schema for users collection."""
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["userId", "email", "firstName", "lastName", "role", "dateJoined", "isActive"],
                "properties": {
                    "_id": {
                        "bsonType": "objectId",
                        "description": "Auto-generated ObjectId"
                    },
                    "userId": {
                        "bsonType": "string",
                        "description": "Unique user identifier"
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{2,}$",
                        "description": "Valid email address"
                    },
                    "firstName": {
                        "bsonType": "string",
                        "description": "User's first name"
                    },
                    "lastName": {
                        "bsonType": "string",
                        "description": "User's last name"
                    },
                    "role": {
                        "enum": ["student", "instructor"],
                        "description": "User role"
                    },
                    "dateJoined": {
                        "bsonType": "date",
                        "description": "Account creation date"
                    },
                    "profile": {
                        "bsonType": "object",
                        "properties": {
                            "bio": {"bsonType": "string"},
                            "avatar": {"bsonType": "string"},
                            "skills": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            }
                        }
                    },
                    "isActive": {
                        "bsonType": "bool",
                        "description": "Account active status"
                    }
                }
            }
        }
    
    @staticmethod
    def get_course_schema() -> Dict:
        """Returns JSON schema for courses collection."""
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["courseId", "title", "instructorId", "level", "duration", "price", "createdAt", "isPublished"],
                "properties": {
                    "_id": {"bsonType": "objectId"},
                    "courseId": {
                        "bsonType": "string",
                        "description": "Unique course identifier"
                    },
                    "title": {
                        "bsonType": "string",
                        "description": "Course title"
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "Course description"
                    },
                    "instructorId": {
                        "bsonType": "string",
                        "description": "Instructor's userId"
                    },
                    "category": {
                        "bsonType": "string",
                        "description": "Course category"
                    },
                    "level": {
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "Course difficulty level"
                    },
                    "duration": {
                        "bsonType": "int",
                        "minimum": 1,
                        "description": "Course duration in hours"
                    },
                    "price": {
                        "bsonType": ["double", "int"],
                        "minimum": 0,
                        "description": "Course price"
                    },
                    "tags": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "createdAt": {"bsonType": "date"},
                    "updatedAt": {"bsonType": "date"},
                    "isPublished": {"bsonType": "bool"}
                }
            }
        }
    
    @staticmethod
    def get_enrollment_schema() -> Dict:
        """Returns JSON schema for enrollments collection."""
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["enrollmentId", "userId", "courseId", "enrolledAt", "status"],
                "properties": {
                    "_id": {"bsonType": "objectId"},
                    "enrollmentId": {"bsonType": "string"},
                    "userId": {"bsonType": "string"},
                    "courseId": {"bsonType": "string"},
                    "enrolledAt": {"bsonType": "date"},
                    "status": {
                        "enum": ["active", "completed", "dropped"],
                        "description": "Enrollment status"
                    },
                    "progress": {
                        "bsonType": "double",
                        "minimum": 0,
                        "maximum": 100
                    }
                }
            }
        }
    
    @staticmethod
    def get_assignment_schema() -> Dict:
        """Returns JSON schema for assignments collection."""
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["assignmentId", "courseId", "title", "dueDate"],
                "properties": {
                    "_id": {"bsonType": "objectId"},
                    "assignmentId": {"bsonType": "string"},
                    "courseId": {"bsonType": "string"},
                    "title": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "dueDate": {"bsonType": "date"},
                    "maxPoints": {
                        "bsonType": "int",
                        "minimum": 0
                    }
                }
            }
        }


class IndexManager:
    """Manages database indexes for optimal query performance."""
    
    @staticmethod
    def create_all_indexes(db: Database):
        """Create all necessary indexes."""
        logger.info("Creating indexes...")
        
        # Users indexes
        db.users.create_index([("userId", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("role", ASCENDING)])
        
        # Courses indexes
        db.courses.create_index([("courseId", ASCENDING)], unique=True)
        db.courses.create_index([("category", ASCENDING)])
        db.courses.create_index([("level", ASCENDING)])
        db.courses.create_index([("instructorId", ASCENDING)])
        db.courses.create_index([("category", ASCENDING), ("level", ASCENDING)])
        db.courses.create_index([("title", TEXT), ("description", TEXT)])
        
        # Enrollments indexes
        db.enrollments.create_index([("enrollmentId", ASCENDING)], unique=True)
        db.enrollments.create_index([("userId", ASCENDING), ("courseId", ASCENDING)])
        db.enrollments.create_index([("enrolledAt", DESCENDING)])
        db.enrollments.create_index([("status", ASCENDING)])
        
        # Assignments indexes
        db.assignments.create_index([("assignmentId", ASCENDING)], unique=True)
        db.assignments.create_index([("courseId", ASCENDING)])
        db.assignments.create_index([("dueDate", ASCENDING)])
        
        # Assignment submissions indexes
        db.assignment_submissions.create_index([("submissionId", ASCENDING)], unique=True)
        db.assignment_submissions.create_index([("assignmentId", ASCENDING), ("userId", ASCENDING)])
        db.assignment_submissions.create_index([("userId", ASCENDING)])
        
        # Lessons indexes
        db.lessons.create_index([("lessonId", ASCENDING)], unique=True)
        db.lessons.create_index([("courseId", ASCENDING)])
        
        logger.info("All indexes created successfully")


class EduHubManager:
    """Main class for managing EduHub operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user_data: Dict) -> Dict[str, Any]:
        """
        Create a new user with validation.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Dictionary with success status and user_id or error message
        """
        try:
            # Validate required fields
            required_fields = ["userId", "email", "firstName", "lastName", "role"]
            for field in required_fields:
                if field not in user_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Add default fields
            user_data["dateJoined"] = datetime.now(timezone.utc)
            user_data.setdefault("isActive", True)
            
            # Insert user
            result = self.db.users.insert_one(user_data)
            logger.info(f"User created: {user_data['userId']}")
            
            return {
                "success": True,
                "user_id": str(result.inserted_id),
                "error": None
            }
            
        except errors.DuplicateKeyError:
            error_msg = f"User with userId '{user_data.get('userId')}' or email '{user_data.get('email')}' already exists"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}
        
        except errors.WriteError as e:
            error_msg = f"Validation error: {e.details.get('errmsg', str(e))}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Find user by email."""
        try:
            user = self.db.users.find_one({"email": email})
            if user:
                logger.info(f"User found: {email}")
            else:
                logger.info(f"User not found: {email}")
            return user
        except Exception as e:
            logger.error(f"Error finding user: {e}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> Dict[str, Any]:
        """Update user profile information."""
        try:
            result = self.db.users.update_one(
                {"userId": user_id},
                {"$set": {"profile": profile_data}}
            )
            
            if result.matched_count == 0:
                return {"success": False, "error": "User not found"}
            
            logger.info(f"User profile updated: {user_id}")
            return {
                "success": True,
                "modified_count": result.modified_count
            }
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return {"success": False, "error": str(e)}
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Soft delete user by setting isActive to False."""
        try:
            result = self.db.users.update_one(
                {"userId": user_id},
                {"$set": {"isActive": False}}
            )
            
            if result.matched_count == 0:
                return {"success": False, "error": "User not found"}
            
            logger.info(f"User deactivated: {user_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== COURSE OPERATIONS ====================
    
    def create_course(self, course_data: Dict) -> Dict[str, Any]:
        """
        Create a new course with validation.
        
        Args:
            course_data: Dictionary containing course information
            
        Returns:
            Dictionary with success status and course_id or error message
        """
        try:
            # Validate required fields
            required_fields = ["courseId", "title", "instructorId", "level", "duration", "price"]
            for field in required_fields:
                if field not in course_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Verify instructor exists
            instructor = self.db.users.find_one({
                "userId": course_data["instructorId"],
                "role": "instructor"
            })
            if not instructor:
                return {"success": False, "error": "Instructor not found"}
            
            # Ensure proper data types
            course_data["duration"] = Int32(course_data["duration"])
            course_data["price"] = float(course_data["price"])
            
            # Add timestamps
            now = datetime.now(timezone.utc)
            course_data["createdAt"] = now
            course_data["updatedAt"] = now
            course_data.setdefault("isPublished", False)
            
            # Insert course
            result = self.db.courses.insert_one(course_data)
            logger.info(f"Course created: {course_data['courseId']}")
            
            return {
                "success": True,
                "course_id": str(result.inserted_id),
                "error": None
            }
            
        except errors.DuplicateKeyError:
            error_msg = f"Course with courseId '{course_data.get('courseId')}' already exists"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}
        
        except Exception as e:
            error_msg = f"Error creating course: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def search_courses(self, 
                       title_keyword: Optional[str] = None,
                       category: Optional[str] = None,
                       level: Optional[str] = None,
                       published_only: bool = True) -> List[Dict]:
        """Search courses with various filters."""
        try:
            query = {}
            
            if title_keyword:
                query["$text"] = {"$search": title_keyword}
            if category:
                query["category"] = category
            if level:
                query["level"] = level
            if published_only:
                query["isPublished"] = True
            
            courses = list(self.db.courses.find(query))
            logger.info(f"Found {len(courses)} courses matching criteria")
            return courses
            
        except Exception as e:
            logger.error(f"Error searching courses: {e}")
            return []
    
    def publish_course(self, course_id: str) -> Dict[str, Any]:
        """Mark a course as published."""
        try:
            result = self.db.courses.update_one(
                {"courseId": course_id},
                {
                    "$set": {
                        "isPublished": True,
                        "updatedAt": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.matched_count == 0:
                return {"success": False, "error": "Course not found"}
            
            logger.info(f"Course published: {course_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error publishing course: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== ENROLLMENT OPERATIONS ====================
    
    def enroll_student(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """
        Enroll a student in a course with validation.
        
        Args:
            user_id: Student's userId
            course_id: Course's courseId
            
        Returns:
            Dictionary with success status and enrollment details
        """
        try:
            # Verify student exists
            student = self.db.users.find_one({
                "userId": user_id,
                "role": "student",
                "isActive": True
            })
            if not student:
                return {"success": False, "error": "Active student not found"}
            
            # Verify course exists and is published
            course = self.db.courses.find_one({
                "courseId": course_id,
                "isPublished": True
            })
            if not course:
                return {"success": False, "error": "Published course not found"}
            
            # Check for existing enrollment
            existing = self.db.enrollments.find_one({
                "userId": user_id,
                "courseId": course_id,
                "status": {"$ne": "dropped"}
            })
            if existing:
                return {"success": False, "error": "Student already enrolled"}
            
            # Create enrollment
            enrollment_count = self.db.enrollments.count_documents({})
            enrollment_data = {
                "enrollmentId": f"E{enrollment_count + 1:03d}",
                "userId": user_id,
                "courseId": course_id,
                "enrolledAt": datetime.now(timezone.utc),
                "status": "active",
                "progress": 0.0
            }
            
            result = self.db.enrollments.insert_one(enrollment_data)
            logger.info(f"Student {user_id} enrolled in course {course_id}")
            
            return {
                "success": True,
                "enrollment_id": str(result.inserted_id),
                "enrollment_data": enrollment_data
            }
            
        except Exception as e:
            error_msg = f"Error enrolling student: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_student_enrollments(self, user_id: str) -> List[Dict]:
        """Get all enrollments for a student with course details."""
        try:
            pipeline = [
                {"$match": {"userId": user_id}},
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
                    "$project": {
                        "enrollmentId": 1,
                        "courseId": 1,
                        "enrolledAt": 1,
                        "status": 1,
                        "progress": 1,
                        "courseTitle": "$course.title",
                        "courseCategory": "$course.category",
                        "courseLevel": "$course.level"
                    }
                },
                {"$sort": {"enrolledAt": -1}}
            ]
            
            enrollments = list(self.db.enrollments.aggregate(pipeline))
            logger.info(f"Retrieved {len(enrollments)} enrollments for user {user_id}")
            return enrollments
            
        except Exception as e:
            logger.error(f"Error getting enrollments: {e}")
            return []
    
    # ==================== ANALYTICS & AGGREGATIONS ====================
    
    def get_course_enrollment_stats(self) -> List[Dict]:
        """Get enrollment statistics for all courses."""
        try:
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
                        "category": "$course.category",
                        "total_enrollments": 1,
                        "active_enrollments": 1,
                        "completed_enrollments": 1,
                        "completion_rate": {
                            "$cond": [
                                {"$eq": ["$total_enrollments", 0]},
                                0,
                                {
                                    "$multiply": [
                                        {"$divide": ["$completed_enrollments", "$total_enrollments"]},
                                        100
                                    ]
                                }
                            ]
                        }
                    }
                },
                {"$sort": {"total_enrollments": -1}}
            ]
            
            stats = list(self.db.enrollments.aggregate(pipeline, allowDiskUse=True))
            logger.info(f"Retrieved enrollment stats for {len(stats)} courses")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting enrollment stats: {e}")
            return []
    
    def get_category_popularity(self) -> List[Dict]:
        """Get enrollment counts by course category."""
        try:
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
            
            stats = list(self.db.enrollments.aggregate(pipeline))
            logger.info(f"Retrieved category popularity stats")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return []
    
    def get_student_performance(self, user_id: str) -> Dict[str, Any]:
        """Get performance metrics for a student."""
        try:
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
            
            result = list(self.db.assignment_submissions.aggregate(pipeline))
            
            if result:
                performance = result[0]
                performance["userId"] = user_id
                logger.info(f"Retrieved performance for user {user_id}")
                return performance
            else:
                return {
                    "userId": user_id,
                    "total_submissions": 0,
                    "average_grade": None,
                    "highest_grade": None,
                    "lowest_grade": None
                }
            
        except Exception as e:
            logger.error(f"Error getting student performance: {e}")
            return {}
    
    # ==================== VISUALIZATION ====================
    
    def plot_enrollment_trends(self, months: int = 12):
        """Plot enrollment trends over time."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
            
            pipeline = [
                {"$match": {"enrolledAt": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$enrolledAt"},
                            "month": {"$month": "$enrolledAt"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]
            
            data = list(self.db.enrollments.aggregate(pipeline))
            
            if not data:
                logger.warning("No enrollment data available for plotting")
                return
            
            # Prepare data for plotting
            dates = [datetime(d["_id"]["year"], d["_id"]["month"], 1) for d in data]
            counts = [d["count"] for d in data]
            
            # Create plot
            plt.figure(figsize=(12, 6))
            plt.plot(dates, counts, marker='o', linewidth=2, markersize=8, color='#2E86DE')
            
            # Formatting
            plt.xlabel('Month', fontsize=12, fontweight='bold')
            plt.ylabel('Enrollments', fontsize=12, fontweight='bold')
            plt.title('Monthly Enrollment Trends', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            
            logger.info("Enrollment trends plotted successfully")
            
        except Exception as e:
            logger.error(f"Error plotting enrollment trends: {e}")
    
    def plot_category_distribution(self):
        """Plot course category distribution."""
        try:
            stats = self.get_category_popularity()
            
            if not stats:
                logger.warning("No category data available for plotting")
                return
            
            categories = [s["category"] for s in stats]
            enrollments = [s["total_enrollments"] for s in stats]
            
            # Create plot
            plt.figure(figsize=(10, 6))
            bars = plt.bar(categories, enrollments, color='#10AC84', alpha=0.8)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontweight='bold')
            
            plt.xlabel('Category', fontsize=12, fontweight='bold')
            plt.ylabel('Total Enrollments', fontsize=12, fontweight='bold')
            plt.title('Course Category Distribution', fontsize=14, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.show()
            
            logger.info("Category distribution plotted successfully")
            
        except Exception as e:
            logger.error(f"Error plotting category distribution: {e}")


# ==================== DATA POPULATION ====================

class DataPopulator:
    """Handles sample data population for testing."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def populate_users(self, count: int = 20):
        """Populate users collection with sample data."""
        users = []
        
        # Instructors
        instructors = [
            {"userId": "U001", "firstName": "Sarah", "lastName": "Johnson", "email": "sarah.johnson@eduhub.com", "role": "instructor"},
            {"userId": "U002", "firstName": "Mark", "lastName": "Smith", "email": "mark.smith@eduhub.com", "role": "instructor"},
        ]
        
        # Students
        for i in range(3, count + 1):
            users.append({
                "userId": f"U{i:03d}",
                "firstName": f"Student{i}",
                "lastName": f"LastName{i}",
                "email": f"student{i}@example.com",
                "role": "student",
            })
        
        # Add common fields
        all_users = instructors + users
        for user in all_users:
            user["dateJoined"] = datetime.now(timezone.utc)
            user["isActive"] = True
            user.setdefault("profile", {
                "bio": f"Bio for {user['firstName']}",
                "skills": ["Python", "MongoDB"]
            })
        
        try:
            result = self.db.users.insert_many(all_users)
            logger.info(f"Inserted {len(result.inserted_ids)} users")
            return True
        except Exception as e:
            logger.error(f"Error populating users: {e}")
            return False
    
    def populate_courses(self):
        """Populate courses collection with sample data."""
        courses = [
            {
                "courseId": "C001",
                "title": "Python for Beginners",
                "description": "Learn Python from scratch",
                "instructorId": "U001",
                "category": "Programming",
                "level": "beginner",
                "duration": Int32(20),
                "price": 50.0,
                "tags": ["python", "programming"],
                "isPublished": True
            },
            {
                "courseId": "C002",
                "title": "Data Analysis with Excel",
                "description": "Master Excel for data analysis",
                "instructorId": "U002",
                "category": "Data Analysis",
                "level": "intermediate",
                "duration": Int32(15),
                "price": 40.0,
                "tags": ["excel", "data"],
                "isPublished": True
            },
            {
                "courseId": "C003",
                "title": "Machine Learning Fundamentals",
                "description": "Introduction to ML concepts",
                "instructorId": "U001",
                "category": "AI/ML",
                "level": "intermediate",
                "duration": Int32(30),
                "price": 80.0,
                "tags": ["machine learning", "ai"],
                "isPublished": True
            },
            {
                "courseId": "C004",
                "title": "Web Development Fundamentals",
                "description": "Learn HTML, CSS, and JavaScript",
                "instructorId": "U002",
                "category": "Web Development",
                "level": "beginner",
                "duration": Int32(25),
                "price": 60.0,
                "tags": ["html", "css", "javascript"],
                "isPublished": True
            },
            {
                "courseId": "C005",
                "title": "Advanced Python",
                "description": "Deep dive into Python",
                "instructorId": "U001",
                "category": "Programming",
                "level": "advanced",
                "duration": Int32(35),
                "price": 100.0,
                "tags": ["python", "advanced"],
                "isPublished": True
            },
        ]
        
        now = datetime.now(timezone.utc)
        for course in courses:
            course["createdAt"] = now
            course["updatedAt"] = now
        
        try:
            result = self.db.courses.insert_many(courses)
            logger.info(f"Inserted {len(result.inserted_ids)} courses")
            return True
        except Exception as e:
            logger.error(f"Error populating courses: {e}")
            return False


# ==================== SETUP AND INITIALIZATION ====================

def setup_database(connection_string: str, reset: bool = False):
    """
    Initialize database with schema validation and indexes.
    
    Args:
        connection_string: MongoDB connection string
        reset: If True, drop existing collections before setup
    """
    logger.info("Starting database setup...")
    
    # Connect to database
    config = DatabaseConfig(connection_string)
    db = config.connect()
    
    # Reset if requested
    if reset:
        logger.warning("Resetting database...")
        for collection in ["users", "courses", "enrollments", "assignments", 
                          "assignment_submissions", "lessons"]:
            db[collection].drop()
        logger.info("Collections dropped")
    
    # Apply schema validation
    logger.info("Applying schema validation...")
    
    # Users collection
    if "users" not in db.list_collection_names():
        db.create_collection("users", validator=SchemaValidator.get_user_schema())
    else:
        db.command({
            "collMod": "users",
            "validator": SchemaValidator.get_user_schema(),
            "validationLevel": "moderate"
        })
    
    # Courses collection
    if "courses" not in db.list_collection_names():
        db.create_collection("courses", validator=SchemaValidator.get_course_schema())
    else:
        db.command({
            "collMod": "courses",
            "validator": SchemaValidator.get_course_schema(),
            "validationLevel": "moderate"
        })
    
    # Enrollments collection
    if "enrollments" not in db.list_collection_names():
        db.create_collection("enrollments", validator=SchemaValidator.get_enrollment_schema())
    else:
        db.command({
            "collMod": "enrollments",
            "validator": SchemaValidator.get_enrollment_schema(),
            "validationLevel": "moderate"
        })
    
    # Assignments collection
    if "assignments" not in db.list_collection_names():
        db.create_collection("assignments", validator=SchemaValidator.get_assignment_schema())
    else:
        db.command({
            "collMod": "assignments",
            "validator": SchemaValidator.get_assignment_schema(),
            "validationLevel": "moderate"
        })
    
    logger.info("Schema validation applied")
    
    # Create indexes
    IndexManager.create_all_indexes(db)
    
    logger.info("Database setup completed successfully")
    return db, config


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function with examples."""
    
    # Configuration
    CONNECTION_STRING = "mongodb+srv://ukosarahiniobong_db_user:rdy3YxtWhgTkNe1P@cluster0.hu4ajdz.mongodb.net/"
    
    # Setup database
    db, config = setup_database(CONNECTION_STRING, reset=False)
    
    # Initialize manager
    manager = EduHubManager(db)
    
    print("\n" + "="*60)
    print("EDUHUB MONGODB PROJECT - DEMONSTRATION")
    print("="*60)
    
    # ==================== DEMO: USER OPERATIONS ====================
    print("\n### USER OPERATIONS ###\n")
    
    # Create a new user
    print("1. Creating a new user...")
    new_user = {
        "userId": "U999",
        "email": "demo.user@eduhub.com",
        "firstName": "Demo",
        "lastName": "User",
        "role": "student",
        "profile": {
            "bio": "Test user for demonstration",
            "skills": ["Python", "MongoDB", "Data Analysis"]
        }
    }
    result = manager.create_user(new_user)
    print(f"   Result: {result}")
    
    # Find user by email
    print("\n2. Finding user by email...")
    user = manager.get_user_by_email("demo.user@eduhub.com")
    if user:
        print(f"   Found: {user['firstName']} {user['lastName']} ({user['role']})")
    
    # ==================== DEMO: COURSE OPERATIONS ====================
    print("\n### COURSE OPERATIONS ###\n")
    
    # Create a new course
    print("1. Creating a new course...")
    new_course = {
        "courseId": "C999",
        "title": "MongoDB Masterclass",
        "description": "Complete guide to MongoDB",
        "instructorId": "U001",
        "category": "Database",
        "level": "intermediate",
        "duration": 40,
        "price": 89.99,
        "tags": ["mongodb", "database", "nosql"]
    }
    result = manager.create_course(new_course)
    print(f"   Result: {result}")
    
    # Search courses
    print("\n2. Searching for Python courses...")
    courses = manager.search_courses(title_keyword="Python")
    print(f"   Found {len(courses)} courses")
    for course in courses[:3]:
        print(f"   - {course['title']} ({course['level']})")
    
    # ==================== DEMO: ENROLLMENT OPERATIONS ====================
    print("\n### ENROLLMENT OPERATIONS ###\n")
    
    # Enroll student
    print("1. Enrolling student in course...")
    result = manager.enroll_student("U999", "C001")
    print(f"   Result: {result}")
    
    # Get student enrollments
    print("\n2. Getting student enrollments...")
    enrollments = manager.get_student_enrollments("U999")
    print(f"   Found {len(enrollments)} enrollments")
    for enrollment in enrollments:
        print(f"   - {enrollment['courseTitle']} (Status: {enrollment['status']})")
    
    # ==================== DEMO: ANALYTICS ====================
    print("\n### ANALYTICS & REPORTS ###\n")
    
    # Course enrollment stats
    print("1. Course enrollment statistics...")
    stats = manager.get_course_enrollment_stats()
    print(f"   Analyzed {len(stats)} courses")
    for stat in stats[:5]:
        print(f"   - {stat['title']}: {stat['total_enrollments']} enrollments "
              f"({stat['completion_rate']:.1f}% completion)")
    
    # Category popularity
    print("\n2. Category popularity...")
    category_stats = manager.get_category_popularity()
    for stat in category_stats:
        print(f"   - {stat['category']}: {stat['total_enrollments']} enrollments, "
              f"{stat['unique_students']} unique students")
    
    # ==================== DEMO: VISUALIZATIONS ====================
    print("\n### VISUALIZATIONS ###\n")
    
    print("Generating enrollment trends chart...")
    manager.plot_enrollment_trends(months=6)
    
    print("Generating category distribution chart...")
    manager.plot_category_distribution()
    
    # ==================== DEMO: ERROR HANDLING ====================
    print("\n### ERROR HANDLING EXAMPLES ###\n")
    
    # Duplicate user
    print("1. Attempting to create duplicate user...")
    result = manager.create_user(new_user)
    print(f"   Result: {result}")
    
    # Invalid enrollment
    print("\n2. Attempting to enroll non-existent student...")
    result = manager.enroll_student("INVALID", "C001")
    print(f"   Result: {result}")
    
    # Missing required field
    print("\n3. Attempting to create course without required fields...")
    invalid_course = {
        "courseId": "C888",
        "title": "Incomplete Course"
        # Missing required fields: instructorId, level, duration, price
    }
    result = manager.create_course(invalid_course)
    print(f"   Result: {result}")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETED")
    print("="*60 + "\n")
    
    # Cleanup
    print("Cleaning up demo data...")
    db.users.delete_one({"userId": "U999"})
    db.courses.delete_one({"courseId": "C999"})
    db.enrollments.delete_many({"userId": "U999"})
    print("Cleanup completed")
    
    # Close connection
    config.close()


# ==================== UTILITY FUNCTIONS ====================

def export_to_csv(db: Database, collection_name: str, filename: str):
    """Export collection data to CSV file."""
    try:
        data = list(db[collection_name].find())
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(data)} documents to {filename}")
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")


def generate_performance_report(db: Database, user_id: str) -> str:
    """Generate a formatted performance report for a student."""
    manager = EduHubManager(db)
    
    # Get enrollments
    enrollments = manager.get_student_enrollments(user_id)
    
    # Get performance
    performance = manager.get_student_performance(user_id)
    
    report = f"""
    {'='*60}
    STUDENT PERFORMANCE REPORT
    {'='*60}
    Student ID: {user_id}
    
    ENROLLMENTS:
    - Total Courses: {len(enrollments)}
    - Active: {sum(1 for e in enrollments if e['status'] == 'active')}
    - Completed: {sum(1 for e in enrollments if e['status'] == 'completed')}
    
    ACADEMIC PERFORMANCE:
    - Total Submissions: {performance.get('total_submissions', 0)}
    - Average Grade: {performance.get('average_grade', 0):.2f}%
    - Highest Grade: {performance.get('highest_grade', 0):.2f}%
    - Lowest Grade: {performance.get('lowest_grade', 0):.2f}%
    
    ENROLLED COURSES:
    """
    
    for enrollment in enrollments:
        report += f"\n    - {enrollment['courseTitle']} ({enrollment['courseCategory']})"
        report += f"\n      Level: {enrollment['courseLevel']}, Progress: {enrollment.get('progress', 0):.1f}%"
    
    report += f"\n    {'='*60}\n"
    
    return report


if __name__ == "__main__":
    # Run main demonstration
    main()
    
    # Additional examples
    print("\n### ADDITIONAL UTILITY EXAMPLES ###\n")
    
    # Connection example for other scripts
    CONNECTION_STRING = "mongodb+srv://ukosarahiniobong_db_user:rdy3YxtWhgTkNe1P@cluster0.hu4ajdz.mongodb.net/"
    config = DatabaseConfig(CONNECTION_STRING)
    db = config.connect()
    
    # Generate performance report
    print("Generating performance report...")
    report = generate_performance_report(db, "U003")
    print(report)
    
    config.close()