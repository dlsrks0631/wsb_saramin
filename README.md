# wsb_saramin

## 프로젝트 소개
사람인 데이터를 활용하여 구인구직 백엔드 서버를 구축한 프로젝트입니다. 이 프로젝트는 **Flask**를 기반으로 구현되었으며, RESTful API를 제공하여 구직자와 채용 정보를 관리하고 검색할 수 있도록 설계되었습니다.

---

## 기능
- 구인/구직 데이터 등록, 수정, 삭제
- 조건 검색 기능 (예: 키워드, 지역, 직무 등)
- 데이터베이스와 연동된 CRUD 작업 수행
- JWT를 사용한 인증 및 권한 관리

---

## 실행 방법

### 1. 사전 준비
1. Python과 pip가 설치되어 있어야 합니다.
   - [Python 다운로드](https://www.python.org/)

2. MySQL 데이터베이스가 설치 및 실행 중이어야 합니다.
   - MySQL 설정 시, 아래의 설정 정보를 참고하세요.

### 2. 레포지토리 클론
```bash
# GitHub에서 레포지토리를 클론합니다.
git clone https://github.com/dlsrks0631/wsb_saramin.git

# 프로젝트 디렉토리로 이동합니다.
cd wsb_saramin
```

### 3. 가상 환경 생성 및 의존성 설치
```bash
# 가상 환경을 생성합니다.
python -m venv venv

# 가상 환경을 활성화합니다.
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 필요한 pip 패키지를 설치합니다.
pip install -r requirements.txt
```

### 4. 환경 변수 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 아래와 같은 내용으로 환경 변수를 설정하세요:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=wsb_saramin
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

### 5. 데이터베이스 설정
1. MySQL에 접속하여 데이터베이스를 생성합니다:
   ```sql
   CREATE DATABASE wsb_saramin;
   ```
2. 데이터베이스 초기 스키마 및 데이터를 적용합니다:
   ```bash
   # 프로젝트 내의 SQL 스크립트를 실행합니다.
   mysql -u root -p wsb_saramin < schema.sql
   ```

### 6. 서버 실행
```bash
# Flask 서버를 실행합니다.
python app.py
```

---

## API 문서
### 주요 엔드포인트
| 메서드 | 엔드포인트          | 설명                       |
|--------|---------------------|----------------------------|
| GET    | `/api/jobs`         | 구인 정보 조회            |
| POST   | `/api/jobs`         | 구인 정보 생성            |
| PUT    | `/api/jobs/:id`     | 구인 정보 수정            |
| DELETE | `/api/jobs/:id`     | 구인 정보 삭제            |
| POST   | `/api/auth/login`   | 사용자 로그인             |

API의 상세 사용법은 프로젝트 내 Swagger 또는 Postman 문서를 참고하세요.

---

## 기술 스택
- **백엔드**: Flask
- **데이터베이스**: MySQL
- **인증**: JWT
- **배포**: (배포 관련 정보가 있다면 추가)

---

## 문의
- [김제현](https://github.com/dlsrks0631)
