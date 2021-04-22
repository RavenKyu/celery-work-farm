# Celery Job Farm  `v1.0.0`
셀러리(Celery)를 사용하여 분산 작업 요청을 처리합니다.
* 수집 데이터 DB에 넣기
* PDF 보고서 파일 생성
* 기타 긴 처리시간을 요구하는 작업

## 단독 테스트
테스트를 위한 브로커 및 레디스 컨테이너 실행
```bash
$ docker-compose -f docker-compose.test.yml up --build
```

웹으로 접속하여 동작 확인. 새로고침시 마다 새로운 작업 수행
`http://localhost:8080`

```bash
BROCKER_URL=redis://localhost:6379/0 
CELERY_RESULT_BACKEND=redis://localhost:6379/0 celery -A job_queue:app worker -l info 
```

## 태스크 목록
### Event Collector Handler
Event Collector 에서 사용하는 태스크 모음
* `action_redis_message_queue_publish` 
  * `Redis`의 메시지큐를 이용하여 퍼블리싱 작업

### Data Collector 
Data Collector 에서 수집된 데이터를 DB등에 저장할때 사용
* `db.influxdb.insert_only_changed_value_case`
  * 이전 데이터와 비교하여 변경점이 있을 경우에만 DB에 값 저장
* `db.influxdb.insert`
  * 받은 데이터 모두 DB에 저장
  