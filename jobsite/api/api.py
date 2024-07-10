# api/api.py
from fastapi import FastAPI, Depends, Query
from database import connect_to_postgres, close_connection
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS settings to allow only the specified origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.head("/")
async def head_root():
    """
    Handler for HEAD requests at the root URL ("/").
    """
    return {"message": "This is a HEAD request."}

@app.get("/")
async def read_root():
    """
    Handler for GET requests at the root URL ("/").
    """
    return {"message": "Welcome to your JobAPI"}

@app.get("/data/company/{company}")
async def get_data_by_company(company: str, db=Depends(connect_to_postgres)):
    query = "SELECT distinct * FROM jobs WHERE scrape_date = (select max(scrape_date) from jobs ) and company ILIKE $1 ORDER BY scrape_date DESC;"
    rows = await db.fetch(query, f"%{company}%")
    await close_connection(db)
    return rows

@app.get("/data/position/")
async def get_data_by_position(position: str = Query(..., description="Position name to search for"), db=Depends(connect_to_postgres)):
    query = "SELECT distinct * FROM jobs WHERE scrape_date = (select max(scrape_date) from jobs ) and vacancy ILIKE $1 ORDER BY scrape_date DESC;"
    rows = await db.fetch(query, f"%{position}%")
    await close_connection(db)
    return rows


@app.get("/data/")
async def get_data(
    company: str = Query(None, description="Company name to search for (partial match)"),
    position: str = Query(None, description="Position name to search for"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    db=Depends(connect_to_postgres)
):
    offset = (page - 1) * page_size

    base_query = "SELECT distinct * FROM jobs WHERE scrape_date = (SELECT MAX(scrape_date) FROM jobs)"
    count_query = "SELECT COUNT(*) FROM jobs WHERE scrape_date = (SELECT MAX(scrape_date) FROM jobs)"

    filters = []
    if company:
        filters.append(f"company ILIKE '%{company}%'")
    if position:
        filters.append(f"vacancy ILIKE '%{position}%'")
    
    if filters:
        filter_query = " AND " + " AND ".join(filters)
        base_query += filter_query
        count_query += filter_query

    query = f"{base_query} ORDER BY scrape_date DESC OFFSET $1 LIMIT $2;"
    rows = await db.fetch(query, offset, page_size)
    total_count = await db.fetchval(count_query)

    await close_connection(db)
    total_pages = (total_count // page_size) + (1 if total_count % page_size > 0 else 0)

    return {
        "results": rows,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count
    }
