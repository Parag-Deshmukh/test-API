from fastapi import APIRouter, Query
from fastapi import Body, HTTPException, Query,Response
from pymongo import  DESCENDING, ASCENDING
from typing import Optional, List
from config.database import courses_collection
from schema import schema



Data=courses_collection
router=APIRouter()


#Endpoint to get a list of all available courses.
@router.get("/courses",response_model=schema.CoursesResponse)
async def get_courses(
    sort_by: str = Query("name", enum=["name", "date", "rating"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    domain: Optional[List[str]] = Query(None)
    
):
   
    query_filter = {}
    if domain:
        query_filter["domain"] = {"$in": domain}  # Filter by domain

    sort_direction = ASCENDING if sort_order == "asc" else DESCENDING

    sort_field_mapping = {
        "name": "name",
        "date": "date",
        "rating": "rating"
    }

    courses = list(Data.find(query_filter).sort(sort_field_mapping[sort_by], sort_direction))
    for course in courses:
        course.pop("_id", None)

    return {"courses": courses}


 ## Endpoint to get the course overview
@router.get("/course-overview/{course_name}", response_model=schema.CourseOverview)
async def get_course_overview(course_name: str):
    course = Data.find_one({"name": course_name}, {"_id": 0, "chapters.contents": 0})

    if course:
        return course  # Directly return the course data without wrapping it in a 'course_overview' key
    else:
        raise HTTPException(status_code=404, detail="Course not found")
    
@router.get("/course-chapter",response_model=schema.CourseChapter)
async def get_course_chapter(course_name: str, chapter_name: str):
    course = Data.find_one(
        {"name": course_name, "chapters.name": chapter_name},
        {"_id": 0, "chapters": {"$elemMatch": {"name": chapter_name}}}
    )

    if not course or not course.get("chapters"):
        raise HTTPException(status_code=404, detail="Course or chapter not found")

    return {"course_name": course_name, "chapter": course["chapters"][0]}



@router.post("/rate-chapter",response_model=schema.RateChapterResponse)
async def rate_chapter(
    course_name: str,
    chapter_name: str,
    rating: str = Body(..., embed=True, regex="^(positive|negative)$")
):
    course = Data.find_one(
        {"name": course_name, "chapters.name": chapter_name}
    )

    if not course:
        raise HTTPException(status_code=404, detail="Course or chapter not found")

    update_query = {
        "name": course_name,
        "chapters.name": chapter_name
    }

    if rating == "positive":
        update_action = {"$inc": {"chapters.$.positive_ratings": 1}}
    else:
        update_action = {"$inc": {"chapters.$.negative_ratings": 1}}

    result = Data.update_one(update_query, update_action)

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Failed to update rating")


    course = Data.aggregate([
        {"$match": {"name": course_name}},
        {"$unwind": "$chapters"},
        {"$group": {
            "_id": "$name",
            "total_positive_ratings": {"$sum": "$chapters.positive_ratings"},
            "total_negative_ratings": {"$sum": "$chapters.negative_ratings"}
        }}
    ])

    course_ratings = list(course)
    if not course_ratings:
        raise HTTPException(status_code=404, detail="Course rating aggregation failed")

    return {
        "course_name": course_ratings[0]["_id"],
        "total_positive_ratings": course_ratings[0]["total_positive_ratings"],
        "total_negative_ratings": course_ratings[0]["total_negative_ratings"]
    }