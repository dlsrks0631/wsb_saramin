import sqlalchemy
from sqlalchemy.sql import text

def create_db_connection():
    """
    데이터베이스 연결 엔진 생성 함수
    """
    try:
        engine = sqlalchemy.create_engine(
            'mysql+pymysql://root:Okay%401120@localhost/saramin?charset=utf8mb4',
            echo=True  # SQLAlchemy 실행 쿼리 로그 출력
        )
        print("데이터베이스 연결 엔진 생성 성공")
        return engine
    except Exception as e:
        print(f"데이터베이스 연결 생성 중 오류 발생: {e}")
        raise

def create_user_table():
    """
    사용자 테이블 생성 함수
    """
    engine = create_db_connection()
    try:
        with engine.connect() as conn:
            print("데이터베이스에 연결 성공")
            conn.execution_options(autocommit=True).execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
            """))
            print("users 테이블이 성공적으로 생성되었거나 이미 존재합니다.")
    except sqlalchemy.exc.OperationalError as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise
    except sqlalchemy.exc.ProgrammingError as e:
        print(f"SQL 실행 오류: {e}")
        raise
    except Exception as e:
        print(f"테이블 생성 중 알 수 없는 오류 발생: {e}")
        raise
