from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse

from backend.app.logging import logger
from backend.app.utils.misc import (
    get_cat_image_url,
    fetch_image,
)

router = APIRouter(
    tags=["misc"],
)


@router.get("/hello")
def hello_func():
    return "Hello World"


@router.get("/cat/{status_code}")
async def cat_by_status(status_code: int):
    try:
        image_url = await get_cat_image_url(status_code)
        image_bytes = await fetch_image(image_url)

        response = StreamingResponse(
            content=iter([image_bytes]), media_type="image/jpeg"
        )

        return response

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content=e.detail)

    except Exception as e:
        logger.error(f"Error fetching cat image: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content="Internal Server Error",
        )