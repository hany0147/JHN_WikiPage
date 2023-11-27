from .models import Post, TotalWord, PostDetail, RelatedPost
import math


def get_word_values(post, common_word):
    '''
    해당 Post에서의 특정 단어의 빈도, TF-IDF값(연관성) 추출하는 함수
    '''
    post_values = PostDetail.objects.filter(post=post, word__word=common_word).values('association', 'frequency').first()
    return post_values['association'], post_values['frequency'] if post_values else (0, 0)


def calculate_association(word, frequency): # 해당 게시글-단어 연관성 계산
    '''
    TF-IDF 개념 도입(단어의 상대적인 중요성 계산)
        - 해당 게시글에서 해당 단어의 연관성 측정 위함
        - 해당 게시글에서 해당 단어의 빈도수 * log(전체 게시글 수 / 해당 단어가 게시글에 나타나는 수)
    '''
    total_posts_count = Post.objects.count()
    word_in_total_count = TotalWord.objects.filter(word=word).values_list('count', flat=True).first()
    
    if word_in_total_count is None or word_in_total_count <= 0:
        print(f'Error: "{word}"에 대한 TotalWord 정보가 없거나 0 또는 음수입니다. 데이터베이스 확인 바랍니다.')
        return None

    else:
        try:
            tfidf = frequency * math.log(total_posts_count / word_in_total_count + 1) # log가 0이되는 걸 방지하기 위해 + 1을 함
            return tfidf
        except Exception as e:
            print(f'"{word}"의 TF-IDF를 계산하는 동안 에러가 발생했습니다: {e}')
            return None
    

def create_related_posts(post):
    '''
    연관 게시글 생성 함수 (게시글이 생성될 때 같이 호출)
        1. 배제 단어(전체 게시글의 60% 이상을 차지하는 단어)를 제외한 나머지 단어에서 기준 게시글과 다른 게시글 간의 공통 단어 추출
        2. 공통 단어가 2개 이상인 경우, 연관 게시글로 판단
        3. 연관 게시글의 연관도 계산
            - 연관 게시글에서 해당 단어들의 빈도합
            - 해당 연관도를 기준으로 정렬
        4. 기준 게시글 또한 연관 게시글의 연관 게시글이므로 역으로 한번더 계산
    '''
    total_posts_count = Post.objects.count()
    threshold = total_posts_count * 0.6
    excluded = TotalWord.objects.filter(count__gte=threshold).values_list('word', flat=True)
    core_words = PostDetail.objects.filter(post=post).exclude(word__in=excluded).values_list('word__word', flat=True)
    if not core_words:
        print('공통 단어가 존재하지 않습니다.')
        return None
    
    related_posts = []
    other_posts = Post.objects.exclude(pk=post.pk)

    for other_post in other_posts:
        other_words = PostDetail.objects.filter(post=other_post).exclude(word__in=excluded).values_list('word__word', flat=True)
        common_words = set(core_words) & set(other_words)
        print(common_words)

        if len(common_words) >= 2:
            post_association, other_association = 0, 0
            for common_word in common_words:
                post_frequency = PostDetail.objects.filter(post=post, word__word=common_word).values_list('frequency', flat=True).first()
                other_frequency = PostDetail.objects.filter(post=other_post, word__word=common_word).values_list('frequency', flat=True).first()

                post_association += other_frequency
                other_association += post_frequency

            related_post, reversed_related_post = None, None
            if post_association != 0: # 연관성이 0이면 연관이 없으므로 연관게시글 생성 x
                related_post = RelatedPost(from_post=post, to_post=other_post, association=post_association)
            if other_association != 0:
                # 연관게시글에서 연관게시글은 기준게시글이 되므로 반대로도 계산해줘야 함
                reversed_related_post = RelatedPost(from_post=other_post, to_post=post, association=other_association)

            if related_post:
                related_posts.append(related_post)
            if reversed_related_post:
                related_posts.append(reversed_related_post)

    return RelatedPost.objects.bulk_create(related_posts)

# def create_related_posts(post):
#     '''
#     연관 게시글 생성 함수 (게시글이 생성될 때 같이 호출)
#         1. 배제 단어(전체 게시글의 60% 이상을 차지하는 단어)를 제외한 나머지 단어에서 기준 게시글과 다른 게시글 간의 공통 단어 추출
#         2. 공통 단어가 2개 이상인 경우, 연관 게시글로 판단
#         3. 연관 게시글의 연관도 계산
#             - SUM(기준 게시글의 TF-IDF값 * 연관 게시글의 빈도)
#             - 해당 연관도를 기준으로 정렬
#         4. 기준 게시글 또한 연관 게시글의 연관 게시글이므로 역으로 한번더 계산
#     '''
#     total_posts_count = Post.objects.count()
#     threshold = total_posts_count * 0.6
#     excluded = TotalWord.objects.filter(count__gte=threshold).values_list('word', flat=True)
#     print('excluded words: ', excluded)
#     core_words = PostDetail.objects.filter(post=post).exclude(word__in=excluded).values_list('word__word', flat=True)
#     if not core_words:
#         print('공통 단어가 존재하지 않습니다.')
#         return None
    
#     related_posts = []
#     other_posts = Post.objects.exclude(pk=post.pk)

#     for other_post in other_posts:
#         other_words = PostDetail.objects.filter(post=other_post).exclude(word__in=excluded).values_list('word__word', flat=True)
#         common_words = set(core_words) & set(other_words)

#         if len(common_words) >= 2:
#             post_association, other_association = 0, 0
#             for common_word in common_words:
#                 post_association, post_frequency = get_word_values(post, common_word)
#                 other_association, other_frequency = get_word_values(other_post, common_word)

#                 post_association += post_association * other_frequency
#                 other_association += other_association * post_frequency

#             related_post, reversed_related_post = None, None
#             if post_association != 0: # 연관성이 0이면 연관이 없으므로 연관게시글 생성 x
#                 related_post = RelatedPost(from_post=post, to_post=other_post, association=post_association)
#             if other_association != 0:
#                 # 연관게시글에서 연관게시글은 기준게시글이 되므로 반대로도 계산해줘야 함
#                 reversed_related_post = RelatedPost(from_post=other_post, to_post=post, association=other_association)

#             if related_post:
#                 related_posts.append(related_post)
#             if reversed_related_post:
#                 related_posts.append(reversed_related_post)

#     return RelatedPost.objects.bulk_create(related_posts)

