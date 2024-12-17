from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from db import create_db_connection
from sqlalchemy.sql import text

# Swagger 블루프린트 설정
swagger_bp = Blueprint('swagger', __name__, url_prefix="/api")

api = Api(
    swagger_bp,
    version="1.0",
    title="SaramIn API",
    description="Swagger를 활용한 Flask API 문서화",
    doc="/swagger"  # Swagger UI 경로
)

# 공통 모델 정의
job_model = api.model('Job', {
    'id': fields.Integer(description='Job ID'),
    'company_name': fields.String(description='회사 이름'),
    'title': fields.String(description='공고 제목'),
    'location': fields.String(description='지역'),
    'job_field': fields.String(description='직무 분야'),
    'category': fields.String(description='카테고리'),
})

user_model = api.model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='사용자 이름'),
    'email': fields.String(description='이메일'),
})

favorite_model = api.model('Favorite', {
    'id': fields.Integer(description='Favorite ID'),
    'user_id': fields.Integer(description='User ID'),
    'job_id': fields.Integer(description='Job ID'),
})

# --------------------- Jobs 네임스페이스 ---------------------
ns_jobs = api.namespace('jobs', description="Job 관련 API")

@ns_jobs.route('/')
class JobList(Resource):
    @api.marshal_list_with(job_model)
    def get(self):
        """모든 채용 공고 가져오기"""
        engine = create_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, company_name, title, location, job_field, category FROM saram")
            ).mappings().all()
        return result

# --------------------- Users 네임스페이스 ---------------------
ns_users = api.namespace('users', description="User 관련 API")

@ns_users.route('/')
class UserList(Resource):
    @api.marshal_list_with(user_model)
    def get(self):
        """모든 사용자 가져오기"""
        engine = create_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email FROM users")
            ).mappings().all()
        return result

    @api.expect(user_model)
    def post(self):
        """새로운 사용자 추가"""
        data = request.json
        engine = create_db_connection()
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, email, password_hash) VALUES (:username, :email, :password_hash)"),
                {"username": data["username"], "email": data["email"], "password_hash": "hashed_password"}
            )
        return {"message": "User created successfully"}, 201

# --------------------- Favorites 네임스페이스 ---------------------
ns_favorites = api.namespace('favorites', description="Favorites 관련 API")

@ns_favorites.route('/')
class FavoriteList(Resource):
    @api.marshal_list_with(favorite_model)
    def get(self):
        """모든 즐겨찾기 가져오기"""
        engine = create_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, user_id, job_id FROM favorites")
            ).mappings().all()
        return result

    @api.expect(favorite_model)
    def post(self):
        """즐겨찾기 추가"""
        data = request.json
        engine = create_db_connection()
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO favorites (user_id, job_id) VALUES (:user_id, :job_id)"),
                {"user_id": data["user_id"], "job_id": data["job_id"]}
            )
        return {"message": "Favorite added successfully"}, 201
