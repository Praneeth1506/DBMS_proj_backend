from fastapi import APIRouter

main_router = APIRouter(tags=["Health"])


@main_router.get("/")
def home():
    """Health check — confirms the API is running."""
    return {"message": "Welcome to the DBMS Project API!"}
