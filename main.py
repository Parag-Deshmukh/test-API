from fastapi import FastAPI
from routers import courses


app = FastAPI()


app.include_router(courses.router)


