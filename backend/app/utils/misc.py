from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from httpx import AsyncClient as HTTPClient

async def get_status_code(request: Request):
  # Extract status code from request 
  status_code = request.status_code
  if status_code is None:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
  return status_code


async def get_cat_image_url(status_code: int = Depends(get_status_code)):
  return f"https://http.cat/{status_code}"


async def fetch_cat_image(image_url: str):
  async with HTTPClient() as client:
    response = await client.get(image_url)
    response.raise_for_status()  # Raise exception for non-200 status codes
    return await response.readasbytes()