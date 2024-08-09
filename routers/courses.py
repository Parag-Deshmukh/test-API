from fastapi import APIRouter, Query
from fastapi import Body, HTTPException, Query,Response
from pymongo import  DESCENDING, ASCENDING
from typing import Optional, List
from config.database import courses_collection
from schema import schema



Data=courses_collection
router=APIRouter()


#Endpoint to get a list of all available courses.
@router.get("/courses", response_model=schema.CoursesResponse)
async def get_courses(
    sort_by: str = Query("name", enum=["name", "date", "rating"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    domain: Optional[List[str]] = Query(None)
):
    query_filter = {}
    if domain:
        query_filter["domain"] = {"$in": domain}  # Filter by domain

    sort_direction = ASCENDING if sort_order == "asc" else DESCENDING

    # Fetch courses based on domain filter
    courses = list(Data.find(query_filter))

    for course in courses:
        course.pop("_id", None)
        total_course_rating = 0

        # Calculate rating for each chapter and aggregate the course rating
        for chapter in course.get('chapters', []):
            chapter_rating = chapter.get('positive_ratings', 0) - chapter.get('negative_ratings', 0)
            chapter['rating'] = chapter_rating  # Add the rating field to each chapter
            total_course_rating += chapter_rating

        # Assign the total course rating
        course['rating'] = total_course_rating

    # Sort courses based on the specified field and order
    sort_field = sort_by
    if sort_field == "rating":
        courses.sort(key=lambda x: x.get(sort_field, 0), reverse=(sort_order == "desc"))
    else:
        courses.sort(key=lambda x: x.get(sort_field, ""), reverse=(sort_order == "desc"))

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



@router.post("/rate-chapter", response_model=schema.RateChapterResponse)
async def rate_chapter(
    course_name: str,
    chapter_name: str,
    rating: str = Body(..., embed=True, regex="^(positive|negative)$")
):
    # Increment the relevant rating
    update_action = {"$inc": {f"chapters.$.{rating}_ratings": 1}}
    if Data.update_one({"name": course_name, "chapters.name": chapter_name}, update_action).modified_count == 0:
        raise HTTPException(status_code=404, detail="Failed to update rating")

    # Recalculate and update total_ratings
    chapter = Data.find_one(
        {"name": course_name, "chapters.name": chapter_name},
        {"chapters.$": 1}
    ).get("chapters", [])[0]
    
    if chapter:
        total_ratings = chapter["positive_ratings"] + chapter["negative_ratings"]
        Data.update_one(
            {"name": course_name, "chapters.name": chapter_name},
            {"$set": {"chapters.$.total_ratings": total_ratings}}
        )
    else:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Aggregate course ratings
    course_ratings = list(Data.aggregate([
        {"$match": {"name": course_name}},
        {"$unwind": "$chapters"},
        {"$group": {
            "_id": "$name",
            "positive_ratings": {"$sum": "$chapters.positive_ratings"},
            "negative_ratings": {"$sum": "$chapters.negative_ratings"}
        }}
    ]))

    if not course_ratings:
        raise HTTPException(status_code=404, detail="Aggregation failed")

    return {
        "course_name": course_ratings[0]["_id"],
        "positive_ratings": course_ratings[0]["positive_ratings"],
        "negative_ratings": course_ratings[0]["negative_ratings"]
    }