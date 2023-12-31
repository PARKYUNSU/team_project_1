import scrapy, requests
from scrapy.http import TextResponse
import datetime
import re
import pandas as pd

# GoodchoiceItem 클래스 정의
class GoodchoiceItem(scrapy.Item):
    date = scrapy.Field()       # 날짜
    platform = scrapy.Field()   # 플랫폼 (여기어때)
    name = scrapy.Field()       # 호텔 이름
    level = scrapy.Field()      # 호텔 등급
    score = scrapy.Field()      # 평점
    review_count = scrapy.Field()  # 리뷰 개수
    location = scrapy.Field()   # 호텔 위치
    room_type = scrapy.Field()  # 객실 유형
    price = scrapy.Field()      # 가격
    link = scrapy.Field()       # 링크

# GoodchoiceSpider 클래스 정의
class GoodchoiceSpider(scrapy.Spider):
    name = "Goodchoice"       # 스파이더 이름
    allow_domain= ["goodchoice.kr/"]  # 크롤링 허용 도메인
    KST = datetime.timezone(datetime.timedelta(hours=9))

    start_date = datetime.date(2023, 8, 1)   # 시작일 = 2023년 8월 1일
    end_date = datetime.date(2023, 8, 5)     # 종료일 = 2023년 8월 5일
    persons = 2   # 검색 인원 수 (예: 2명)

    start_urls = ["https://www.dailyhotel.com/"]   # 시작 URL
    data_list = []   # 수집한 데이터를 저장할 리스트

    def start_requests(self):
        KST = datetime.timezone(datetime.timedelta(hours=9))

        gu_code = ['2012']   # 지역 코드 (여기서는 2012로 고정)
        current_date = self.start_date
        while current_date < self.end_date:
            start_date_str = current_date.strftime("%Y-%m-%d")
            end_date_str = (current_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            for gu in gu_code:
                # 지역 코드와 날짜를 포함한 URL 생성
                start_url = f'https://www.goodchoice.kr/product/search/2/{gu}?sort=HIT\
                &sel_date={start_date_str}&sel_date2={end_date_str}&persons={self.persons}'
                yield scrapy.Request(start_url, callback=self.parse, meta={'current_date': current_date})
            current_date += datetime.timedelta(days=1)

    def parse(self, response):
        links = response.xpath('//*[@id="poduct_list_area"]/li/a/@href').extract()
        for link in links:
            yield scrapy.Request(link, callback=self.parse_content, meta={'current_date': response.meta['current_date']})

    def parse_content(self, response):
        KST = datetime.timezone(datetime.timedelta(hours=9))
        date_for_column = response.meta['current_date']  # 현재 처리 중인 날짜를 메타 데이터에서 가져옴
        # 날짜
        date = date_for_column
        # 호텔 이름
        name = response.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/h2/text()')[0].extract()
        # 호텔 등급
        level = response.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/span/text()')[0].extract()
        # 평점
        try:
            tmp = response.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/div[1]/span/text()')[0].extract()
            score = round(float(tmp)/2, 1)
        except:
            score = float(0)
        # 호텔 위치
        location = response.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/p[2]/text()')[0].extract()
        # 객실 유형
        try:
            roomtype = response.xpath('//*[@id="product_filter_form"]/article/div/strong/text()')[1:].extract()
        except:
            roomtype = ['예약만실']
        # 가격
        price = []
        for num in range(2, 2+len(roomtype)):
            try:
                tmp = response.xpath(f'//*[@id="product_filter_form"]/article/div[{num}]/div[3]/div/div/div/p[2]/b/text()')[0].extract()
                tmp = tmp.replace(',',"")
                tmp = tmp.replace('원','')
                price.append(int(tmp))
            except:
                price.append(int(0))
        # 리뷰 개수 (link에 직접 담겨있지 않으며 link url의 hotel_id로 request url 재구성 필요)
        hotel_id = re.findall("ano\=([0-9]+)\&", response.url)[0]
        review_url = 'https://www.goodchoice.kr/product/get_review_non'
        params = {"page": 0, "ano": hotel_id}
        response2 = requests.post(review_url, params)
        review = float(re.findall('"count":([0-9]+)', response2.text)[0])
        # 링크
        hotel_desc_url = response.url
        # 플랫폼
        platform = "여기어때"

        # Item 객체 생성 및 데이터 저장
        item = GoodchoiceItem()
        for i in range(len(roomtype)):
            item['date'] = date
            item['platform'] = platform
            item['name'] = name
            item['level'] = level
            item['score'] = score
            item['review_count'] = review
            item['location'] = location
            item['room_type'] = roomtype[i]
            item['price'] = price[i]
            item['link'] = hotel_desc_url

            self.data_list.append({
                'date': date,
                'platform': platform,
                'name': name,
                'level': level,
                'score': score,
                'review_count': review,
                'location': location,
                'room_type': roomtype[i],
                'price': price[i],
                'link': hotel_desc_url
            })

        yield item

    def closed(self, reason):
        # 데이터를 pandas DataFrame으로 변환
        data_frame = pd.DataFrame(self.data_list)

        # 데이터를 CSV 파일로 저장
        data_frame.to_csv('/content/sample_data/output.csv', index=False, encoding='utf-8-sig')