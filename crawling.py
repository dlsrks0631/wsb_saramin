import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from retrying import retry
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 페이지 요청 함수 (재시도 포함)
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_page(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

# 채용 공고 데이터 파싱 함수
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
            '회사명': company,
            '제목': title,
            '링크': link,
            '지역': location,
            '연봉정보': salary,
            '마감일': deadline,
            '직무분야': sector,
            '카테고리': categories
        }
    except AttributeError as e:
        logging.error(f"항목 파싱 중 에러 발생: {e}")
        return None

# 사람인 크롤링 함수
def crawl_saramin(keyword, pages=10, min_count=120):
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
            
            # 최소 개수 도달 시 중단
            if len(jobs) >= min_count:
                break
            
            page += 1
            time.sleep(1)
            
            # 지정한 페이지 수 도달 후도 부족하면 계속 진행할지 결정 가능
            # 여기서는 pages는 초기 크롤링 범위로, min_count 넘을 때까지 계속 시도
            # pages가 최대 페이지 제한이라면 if page > pages: break 로 제한 가능
        except Exception as e:
            logging.error(f"페이지 요청 중 에러 발생: {e}")
            break
    
    df_jobs = pd.DataFrame(jobs).drop_duplicates(subset=['링크'])
    return df_jobs

if __name__ == "__main__":
    # "python" 키워드로 최소 120개 크롤링 시도
    df = crawl_saramin('python', pages=10, min_count=120)
    
    if df.empty:
        logging.error("크롤링 결과가 비어 있습니다.")
    else:
        # 엑셀로 저장
        df.to_excel("saramin_jobs_120.xlsx", index=False)
        logging.info("엑셀 저장 완료")
