import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from retrying import retry
import time
import sqlalchemy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_page(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_job(job):
    try:
        company = job.select_one('.corp_name a').text.strip()
        title = job.select_one('.job_tit a').text.strip()
        link = 'https://www.saramin.co.kr' + job.select_one('.job_tit a')['href']
        conditions = job.select('.job_condition span')
        location = conditions[0].text.strip() if len(conditions) > 0 else ''
        salary_badge = job.select_one('.area_badge .badge')
        salary = salary_badge.text.strip() if salary_badge else ''
        deadline = job.select_one('.job_date .date').text.strip()
        sector = job.select_one('.job_sector').text.strip() if job.select_one('.job_sector') else ''
        categories = sector.split(', ') if sector else []
        
        return {
            'company': company,
            'title': title,
            'link': link,
            'location': location,
            'salary_info': salary,
            'deadline': deadline,
            'sector': sector,
            'categories': ', '.join(categories)
        }
    except AttributeError as e:
        logging.error(f"항목 파싱 중 에러 발생: {e}")
        return None

def crawl_saramin(keyword, min_count=120):
    jobs = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = 1
    
    while True:
        url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword={keyword}&recruitPage={page}"
        try:
            data = fetch_page(url, headers)
            soup = BeautifulSoup(data, 'html.parser')
            job_listings = soup.select('.item_recruit')
            if not job_listings:
                logging.info("더 이상 공고가 없습니다.")
                break
            
            for job in job_listings:
                parsed_job = parse_job(job)
                if parsed_job:
                    jobs.append(parsed_job)
            
            logging.info(f"{page}페이지 크롤링 완료. 현재 수집된 공고 수: {len(jobs)}")
            
            if len(jobs) >= min_count:
                break
            
            page += 1
            time.sleep(1)
        except Exception as e:
            logging.error(f"페이지 요청 중 에러 발생: {e}")
            break
    
    df_jobs = pd.DataFrame(jobs).drop_duplicates(subset=['link'])
    return df_jobs

def create_db_connection():
    # 본인의 MySQL 환경에 맞추어 user, password, host, dbname 수정
    engine = sqlalchemy.create_engine('mysql+pymysql://root:password@localhost/job_db?charset=utf8mb4')
    return engine

def save_to_mysql(df, engine, table_name='jobs'):
    try:
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        logging.info(f"{table_name} 테이블에 데이터 저장 완료")
    except Exception as e:
        logging.error(f"{table_name} 테이블 저장 중 에러 발생: {e}")

if __name__ == "__main__":
    df = crawl_saramin('python', min_count=120)
    if df.empty:
        logging.error("크롤링 결과가 비어 있습니다.")
    else:
        engine = create_db_connection()
        save_to_mysql(df, engine, 'jobs')
