from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="backend/templates")

from backend.app.database.instance import get_session
from backend.app.core.logging import logger
from backend.app.utils.misc import get_cat_image_url, fetch_image
from backend.app.utils.healthcheck import (
    is_server_live,
    is_memory_usage_within_limits,
    is_database_healthy,
    is_cache_healthy,
    healthcheck_dict,
)

router = APIRouter(tags=["Miscelaneous"])


@router.get("/hello")
def hello_func():
    return "Hello World"


@router.get("/cat/{status_code}")
async def cat_by_status(status_code: int):
    try:
        image_url = get_cat_image_url(status_code)
        image_bytes = await fetch_image(image_url)

        response = StreamingResponse(content=iter([image_bytes]), media_type="image/jpeg")

        return response

    except HTTPException as e:
        logger.error(f"Error fetching cat image: {e}")
        return JSONResponse(status_code=e.status_code, content=e.detail)

    except Exception as e:
        logger.error(f"Error fetching cat image: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content="Internal Server Error"
        )


@router.get("/cat/page/{status_code}", response_class=HTMLResponse)
async def cat_page(request: Request, status_code: int):
    cat_image_url = get_cat_image_url(status_code)

    context = {
        "request": request, 
        "cat_image_url": cat_image_url, 
        "status_code": status_code
    }
    return templates.TemplateResponse("cat_page.html", context=context)

