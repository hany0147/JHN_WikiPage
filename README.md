# JHN_WikiPage: 코딩허브 실무과제
- 개발자: 장하늬

## 주요 기능
- 게시글 목록 조회 (posts/)
- 게시글 상세 조회 (posts/<post_pk>)
  - 제목, 내용, 작성시간
  - 연관 게시글 조회(연관도 높은 순으로 정렬)
- 게시글 생성 (posts/create)
  - 게시글 생성시 연관 게시글도 동시에 생성됨
- 연관단어 데이터 및 그래프 생성 (posts/related_words)

## 프레임워크 및 라이브러리
- Django 3.2.18
- Python 3.9

- 단어 전처리 및 계산
  - Konlpy 0.6.0(명사 위주 단어 분석 위함)
    - **JDK 1.7 이상 버전 설치 요함**
  - scikit-learn==1.3.2

- 연관단어 네트워크
  - matplotlib==3.8.2
  - networkx==3.2.1
  - numpy==1.26.2

## 더미 데이터
- .gitignore에서 db.sqlite3를 제외하였으므로, 필요시 활용가능.
- 불필요하다면 sqlite3 삭제 후 migrate하기 바람