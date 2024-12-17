from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_db_connection
from sqlalchemy.sql import text
import sqlalchemy
from functools import wraps

auth_blueprint = Blueprint('auth', __name__)

# 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("로그인이 필요합니다.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# 회원가입
@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)
        engine = create_db_connection()

        try:
            with engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(text("""
                    SELECT COUNT(*) AS count FROM users
                    WHERE username = :username OR email = :email
                    """), {"username": username, "email": email})
                    if result.scalar() > 0:
                        flash("이미 존재하는 사용자명 또는 이메일입니다.", "error")
                        return redirect(url_for("auth.register"))

                    conn.execute(text("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (:username, :email, :password_hash)
                    """), {"username": username, "email": email, "password_hash": password_hash})
                flash("회원가입이 완료되었습니다. 로그인하세요!", "success")
                return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"회원가입 중 오류 발생: {e}", "error")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

# 로그인
@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        engine = create_db_connection()
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                SELECT * FROM users WHERE email = :email
                """), {"email": email})
                user = result.mappings().first()

            if user and check_password_hash(user["password_hash"], password):
                session['user'] = user["username"]
                flash("로그인에 성공했습니다!", "success")
                return redirect(url_for("home"))
            else:
                flash("이메일 또는 비밀번호가 잘못되었습니다.", "error")
        except Exception as e:
            flash(f"로그인 중 오류 발생: {e}", "error")

    return render_template("login.html")

# 마이페이지
@auth_blueprint.route("/mypage", methods=["GET", "POST"])
@login_required
def mypage():
    engine = create_db_connection()
    current_user = session['user']

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        current_password = request.form.get("current_password")
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        try:
            with engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(text("""
                    SELECT password_hash FROM users WHERE username = :username
                    """), {"username": current_user})
                    user = result.mappings().first()

                    if not user or not check_password_hash(user["password_hash"], current_password):
                        flash("현재 비밀번호가 올바르지 않습니다.", "error")
                        return redirect(url_for("auth.mypage"))

                    if new_password and new_password != confirm_password:
                        flash("새 비밀번호가 일치하지 않습니다.", "error")
                        return redirect(url_for("auth.mypage"))

                    update_query = """
                    UPDATE users SET username = :username, email = :email
                    """
                    params = {"username": username, "email": email, "current_user": current_user}

                    if new_password:
                        password_hash = generate_password_hash(new_password)
                        update_query += ", password_hash = :password_hash"
                        params["password_hash"] = password_hash

                    update_query += " WHERE username = :current_user"
                    conn.execute(text(update_query), params)

                session['user'] = username
                flash("정보가 성공적으로 수정되었습니다!", "success")
                return redirect(url_for("home"))
        except Exception as e:
            flash(f"정보 수정 중 오류 발생: {e}", "error")
            return redirect(url_for("auth.mypage"))

    with engine.connect() as conn:
        user = conn.execute(text("""
        SELECT username, email FROM users WHERE username = :username
        """), {"username": current_user}).mappings().first()

    return render_template("mypage.html", user=user)

@auth_blueprint.route("/favorite/add", methods=["POST"])
@login_required
def add_favorite():
    current_user = session['user']
    job_id = request.json.get("job_id")

    if not job_id:
        return jsonify({"success": False, "msg": "유효하지 않은 공고입니다."})

    try:
        job_id = int(job_id)  # job_id를 정수로 변환
    except ValueError:
        return jsonify({"success": False, "msg": "잘못된 공고 ID입니다."})

    engine = create_db_connection()
    try:
        with engine.connect() as conn:
            # job_id가 실제 saram 테이블에 존재하는지 확인
            job_exists = conn.execute(text("""
                SELECT COUNT(*) FROM saram WHERE id = :job_id
            """), {"job_id": job_id}).scalar()

            if not job_exists:
                return jsonify({"success": False, "msg": "존재하지 않는 공고입니다."})

            # favorite_jobs에 삽입
            conn.execute(text("""
                INSERT INTO favorite_jobs (user_id, job_id)
                SELECT id, :job_id FROM users WHERE username = :username
            """), {"job_id": job_id, "username": current_user})

            conn.commit()  # 명시적으로 트랜잭션 커밋
        return jsonify({"success": True, "msg": "즐겨찾기에 추가되었습니다."})
    except sqlalchemy.exc.IntegrityError:
        return jsonify({"success": False, "msg": "이미 즐겨찾기에 추가된 공고입니다."})
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"success": False, "msg": f"오류 발생: {e}"})

@auth_blueprint.route("/favorite/delete", methods=["POST"])
@login_required
def delete_favorite():
    current_user = session['user']
    job_id = request.json.get("job_id")

    engine = create_db_connection()

    try:
        with engine.connect() as conn:
            # 트랜잭션 시작
            trans = conn.begin()

            # 사용자 ID 가져오기
            user_result = conn.execute(text("""
                SELECT id FROM users WHERE username = :username
            """), {"username": current_user})
            user = user_result.mappings().first()

            if not user:
                return jsonify({"success": False, "msg": "사용자 정보를 찾을 수 없습니다."})

            user_id = user['id']

            # 즐겨찾기 삭제
            result = conn.execute(text("""
                DELETE FROM favorite_jobs
                WHERE user_id = :user_id AND job_id = :job_id
            """), {"user_id": user_id, "job_id": job_id})

            if result.rowcount > 0:
                trans.commit()  # 명시적으로 트랜잭션 커밋
                return jsonify({"success": True, "msg": "즐겨찾기에서 삭제되었습니다."})
            else:
                trans.rollback()  # 삭제할 항목이 없으면 롤백
                return jsonify({"success": False, "msg": "해당 즐겨찾기 항목을 찾을 수 없습니다."})
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"success": False, "msg": f"오류 발생: {e}"})




@auth_blueprint.route("/mypage/favorites", methods=["GET"])
@login_required
def view_favorites():
    current_user = session['user']
    engine = create_db_connection()

    with engine.connect() as conn:
        favorites = conn.execute(text("""
            SELECT saram.* FROM saram
            JOIN favorite_jobs ON saram.id = favorite_jobs.job_id
            JOIN users ON favorite_jobs.user_id = users.id
            WHERE users.username = :username
        """), {"username": current_user}).mappings().all()

    if not favorites:
        flash("즐겨찾기 목록이 비어 있습니다.", "info")

    return render_template("favorites.html", favorites=favorites)


# 로그아웃
@auth_blueprint.route("/logout")
def logout():
    session.pop('user', None)
    flash("로그아웃 되었습니다.", "success")
    return redirect(url_for("home"))

# 비밀번호 확인
@auth_blueprint.route("/check_password", methods=["POST"])
@login_required
def check_password():
    current_password = request.json.get("current_password", "")
    engine = create_db_connection()
    current_user = session['user']

    print(f"현재 비밀번호 입력값: {current_password}, 사용자: {current_user}")  # 디버깅 로그 추가

    with engine.connect() as conn:
        result = conn.execute(text("""
        SELECT password_hash FROM users WHERE username = :username
        """), {"username": current_user})
        user = result.mappings().first()

    if user and check_password_hash(user["password_hash"], current_password):
        print("비밀번호 일치")  # 로그
        return jsonify({"success": True, "msg": "비밀번호가 올바릅니다."})
    else:
        print("비밀번호 불일치")  # 로그
        return jsonify({"success": False, "msg": "비밀번호가 틀렸습니다."})