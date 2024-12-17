from flask import Flask, render_template, request
from flask_jwt_extended import JWTManager
from swagger import swagger_bp  # Swagger 블루프린트 가져오기
from auth import auth_blueprint
from db import create_user_table, create_db_connection
import datetime
from sqlalchemy.sql import text  # text 함수 import

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# JWT 설정
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"
jwt = JWTManager(app)

# Swagger 블루프린트 등록
app.register_blueprint(swagger_bp)

# 기존 블루프린트 등록
app.register_blueprint(auth_blueprint)

@app.route("/", methods=["GET"])
def home():
    # 검색어 및 필터 가져오기
    search_query = request.args.get("q", "").strip()
    location_filter = request.args.get("location", "").strip()
    job_field_filter = request.args.get("job_field", "").strip()
    category_filter = request.args.get("category", "").strip()
    page = int(request.args.get("page", 1))
    jobs_per_page = 20
    offset = (page - 1) * jobs_per_page

    # 데이터베이스에서 채용 공고 가져오기
    engine = create_db_connection()
    with engine.connect() as conn:
        query = """
        SELECT id, company_name, title, link, location, salary_info, deadline, job_field, category
        FROM saram WHERE 1=1
        """
        params = {"limit": jobs_per_page, "offset": offset}

        if search_query:
            query += " AND (company_name LIKE :query OR title LIKE :query)"
            params["query"] = f"%{search_query}%"
        if location_filter:
            query += " AND location = :location"
            params["location"] = location_filter
        if job_field_filter:
            query += " AND job_field = :job_field"
            params["job_field"] = job_field_filter
        if category_filter:
            query += " AND category = :category"
            params["category"] = category_filter

        query += " LIMIT :limit OFFSET :offset"
        jobs = conn.execute(text(query), params).mappings().all()

        # 총 공고 수
        total_count = conn.execute(
            text("SELECT COUNT(*) FROM saram WHERE 1=1"),
            params
        ).scalar()

    # 총 페이지 수 계산
    total_pages = (total_count + jobs_per_page - 1) // jobs_per_page

    # 고유 필터 데이터 가져오기
    locations, job_fields, categories = get_unique_filters()

    return render_template(
        "home.html",
        jobs=jobs,
        search_query=search_query,
        page=page,
        total_pages=total_pages,
        unique_locations=locations,
        unique_job_fields=job_fields,
        unique_categories=categories,
    )

def get_unique_filters():
    """데이터베이스에서 필터링에 필요한 고유 값 가져오기"""
    engine = create_db_connection()
    with engine.connect() as conn:
        locations = conn.execute(text("SELECT DISTINCT location FROM saram")).scalars().all()
        job_fields = conn.execute(text("SELECT DISTINCT job_field FROM saram")).scalars().all()
        categories = conn.execute(text("SELECT DISTINCT category FROM saram")).scalars().all()
    return locations, job_fields, categories

@app.route("/contact", methods=["GET"])
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    create_user_table()
    app.run(host="0.0.0.0", port=4000, debug=True)
