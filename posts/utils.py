from .models import Post, TotalWord, PostDetail, RelatedPost

def calculate_association(post, other_post, common_words):
    '''
    연관 게시글의 연관도 계산 함수(연관 게시글에서 해당 단어들의 빈도합)
    '''
    post_association, other_association = 0, 0

    for common_word in common_words:
        post_frequency = PostDetail.objects.filter(post=post, word__word=common_word).values_list('frequency', flat=True).first()
        other_frequency = PostDetail.objects.filter(post=other_post, word__word=common_word).values_list('frequency', flat=True).first()

        if post_frequency is not None:
            post_association += other_frequency
        if other_frequency is not None:
            other_association += post_frequency

    return post_association, other_association

def create_related_posts(post):
    '''
    연관 게시글 생성 함수 (게시글이 생성될 때 같이 호출)
        1. 배제 단어(전체 게시글의 60% 이상을 차지하는 단어)를 제외한 나머지 단어에서 기준 게시글과 다른 게시글 간의 공통 단어 추출
        2. 공통 단어가 2개 이상인 경우, 연관 게시글로 판단
        3. 연관 게시글의 연관도 계산
            - 연관 게시글에서 해당 단어들의 빈도합
            - 해당 연관도를 기준으로 정렬
        4. 기준 게시글 또한 연관 게시글의 연관 게시글이므로 역으로 한번더 계산(other_post의 association도 구함)
    '''
    total_posts_count = Post.objects.count()
    EXCLUSION_THRESHOLD = total_posts_count * 0.6
    excluded = TotalWord.objects.filter(count__gte=EXCLUSION_THRESHOLD.values_list('word', flat=True))
    base_words = PostDetail.objects.filter(post=post).exclude(word__in=excluded).values_list('word__word', flat=True)

    if not base_words:
        return None
    
    related_posts = []
    other_posts = Post.objects.exclude(pk=post.pk)

    for other_post in other_posts:
        other_words = PostDetail.objects.filter(post=other_post).exclude(word__in=excluded).values_list('word__word', flat=True)
        common_words = set(base_words) & set(other_words)

        if len(common_words) >= 2:
            post_association, other_association = calculate_association(post, other_post, common_words)

            if post_association != 0:
                related_post = RelatedPost(from_post=post, to_post=other_post, association=post_association)
                related_posts.append(related_post)

            if other_association != 0:
                reversed_related_post = RelatedPost(from_post=other_post, to_post=post, association=other_association)
                related_posts.append(reversed_related_post)

    return RelatedPost.objects.bulk_create(related_posts)
