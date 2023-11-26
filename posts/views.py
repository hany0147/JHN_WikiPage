from django.shortcuts import render, redirect
from .models import Post, TotalWord, PostDetail, RelatedPost
from .forms import PostForm
from sklearn.feature_extraction.text import CountVectorizer
from pprint import pprint
import math


def index(request):
    posts = Post.objects.all().order_by('-created_at')

    context = {
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)


def get_word_values(post, common_word):
    post_values = PostDetail.objects.filter(post=post, word__word=common_word).values('association', 'frequency').first()
    return post_values['association'], post_values['frequency'] if post_values else (0, 0)


def create_related_posts(post):
    total_posts_count = Post.objects.count()
    threshold = total_posts_count * 0.6

    excluded = TotalWord.objects.filter(count__gte=threshold).values_list('word', flat=True)
    print('excluded words: ', excluded)
    core_words = PostDetail.objects.filter(post=post).exclude(word__in=excluded).values_list('word__word', flat=True)
    if not core_words:
        print('공통 단어가 존재하지 않습니다.')
        return None
    
    related_posts = []
    other_posts = Post.objects.exclude(pk=post.pk)
    
    for other_post in other_posts:
        other_words = PostDetail.objects.filter(post=other_post).exclude(word__in=excluded).values_list('word__word', flat=True)
        common_words = set(core_words) & set(other_words)

        if len(common_words) >= 2:
            post_association, other_association = 0, 0
            for common_word in common_words:
                post_association, post_frequency = get_word_values(post, common_word)
                other_association, other_frequency = get_word_values(other_post, common_word)

                post_association += post_association * other_frequency
                other_association += other_association * post_frequency

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


def calculate_association(word, frequency): # 해당 게시글-단어 연관성 계산
    '''
    TF-IDF 개념 도입(단어의 상대적인 중요성 계산)
    해당 단어가 40% 미만인지, 여부 확인하기
    아니라면, return None
    맞다면, return tfidf
    tfidf 구하기: frequency * math.log(total_posts_count / word_in_total_count)
    word_in_total_count 구하기: TotalWord.objects.filter(word=word).values('count').first()
    '''
    total_posts_count = Post.objects.count()
    threshold = total_posts_count * 0.6 # 이 부분이 고민된다. 60% 이상과 40% 미만 의 기준이라면 전체 게시글 30개 중 18개 이상의 게시글에 존재하는 단어는 제외하라는 말인데, 즉, 이뜻은 17개이하 게시글에 등장하는 단어부터는 연관게시글 단어 기준으로 택해도 된다는 말인데...40%이하라는 의미는 12개 이하의 게시글을 의미하는 것이고...이렇게 되면, 13~17개 게시글에 쓰이는 단어는 어디에도 속하지 않게됨. 이게 헷갈림
    word_in_total_count = TotalWord.objects.filter(word=word).values_list('count', flat=True).first()
    
    if word_in_total_count < threshold:
        try:
            tfidf = frequency * math.log(total_posts_count / word_in_total_count)
            return tfidf
        except Exception as e:
            print(f'"{word}"의 TF-IDF를 계산하는 동안 에러가 발생했습니다: {e}')
            return None
    elif word_in_total_count is None or word_in_total_count <= 0:
        print(f'Error: "{word}"에 대한 TotalWord 정보가 없거나 0 또는 음수입니다. 데이터베이스 확인 바랍니다.')
        return None
    else:
        print(f'해당 게시글의 "{word}"는 전체 게시글의 60% 이상을 차지하는 단어입니다.')
        return None


def create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save()

            # 단어 저장
            content = [request.POST['content'].lower()]
            vectorizer = CountVectorizer()
            frequency = vectorizer.fit_transform(content)
            words = vectorizer.get_feature_names_out()
            word_cnts = dict(zip(words, frequency.toarray()[0]))

            for word, frequency in word_cnts.items():
                total_word, created = TotalWord.objects.get_or_create(word=word)
                if not created:
                    total_word.count += 1
                total_word.save()
    
                association = calculate_association(word, frequency) # TF-IDF 개념 도입(단어의 상대적인 중요성 계산)
                post_detail = PostDetail(post=post, word=total_word, frequency=frequency, association=association)
                post_detail.save()

            # 연관게시글 생성
            create_related_posts(post)

            return redirect('posts:detail', post.pk)
    else:
        form = PostForm()

    context = {
        'form': form,
    }

    return render(request, 'posts/create.html', context)

def detail(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    related_posts = RelatedPost.objects.filter(from_post=post).order_by('-association')
    context = {
        'post': post,
        'related_posts': related_posts,
    }

    return render(request, 'posts/detail.html', context)