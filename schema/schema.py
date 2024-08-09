from typing import List, Dict, Any
from pydantic import BaseModel

# Model for course chapter
class Chapter(BaseModel):
    name: str
    text: str

# Model for a course
class Course(BaseModel):
    name: str
    date: int  # Unix timestamp
    description: str
    domain: List[str]
    chapters: List[Chapter]

# Model for the response of getting courses
class CoursesResponse(BaseModel):
    courses: List[Course]

# Model for course overview (same as Course but can be expanded if needed)
class CourseOverview(BaseModel):
    name: str
    date: int
    description: str
    domain: List[str]
    chapters: List[Dict[str, Any]]

# Model for course chapter
class CourseChapter(BaseModel):
    course_name: str
    chapter: Chapter

# Model for rating chapter response
class RateChapterResponse(BaseModel):
    course_name: str
    total_positive_ratings: int
    total_negative_ratings: int

# Model for error response
class ErrorResponse(BaseModel):
    error: str
