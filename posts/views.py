from django.shortcuts import render, redirect
from .models import Post, TotalWord, PostDetail, RelatedPost
from .forms import PostForm
from .utils import calculate_association, create_related_posts
from sklearn.feature_extraction.text import CountVectorizer
import re
from konlpy.tag import Okt
import numpy as np
from matplotlib import font_manager
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

def index(request):
    posts = Post.objects.all().order_by('-created_at')

    context = {
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)

def create(request):
    '''
    utils.py에 설명 기재함
    '''
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save()

            # 단어 저장
            content = request.POST['content'].lower()
            okt = Okt()
            okt_content = []
            pos_result = okt.pos(content, norm=True, stem=True)
            okt_nouns = [word for word, pos in pos_result if pos in ['Noun', 'Alpha']]
            okt_content.append(' '.join(okt_nouns))
            vectorizer = CountVectorizer()
            frequency = vectorizer.fit_transform(okt_content)
            words = vectorizer.get_feature_names_out()
            word_cnts = dict(zip(words, frequency.toarray()[0]))

            for word, frequency in word_cnts.items():
                total_word, created = TotalWord.objects.get_or_create(word=word)
                if not created:
                    total_word.count += 1
                total_word.save()
    
                
                post_detail = PostDetail(post=post, word=total_word, frequency=frequency)
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

matplotlib.use("Agg") # GUI 사용하지 않고 그래프 생성하기 위함

def related_words(request):

    # 전체 게시글 호출 후 단어 전처리
    all_posts = Post.objects.all()
    total_contents = [re.sub(r'[^\s\dA-Za-z가-힣]', ' ', post.content.replace('\r\n', ' ')) for post in all_posts]
    fixed_total_contents = [] # 전처리한 전체 게시글 모음 담을 리스트
    for total_content in total_contents:
        okt = Okt()
        pos_result = okt.pos(total_content, norm=True, stem=True)
        nouns = [word for word, pos in pos_result if pos in ['Noun', 'Alpha']]
        fixed_total_contents.append(' '.join(nouns))

    # DTM 자료 생성(Document-Term Matrix: 문서(행)와 단어(열)간의 관계를 나타내는 매트릭스)
    countervectorizer = CountVectorizer(max_features=50)
    dtm = countervectorizer.fit_transform(fixed_total_contents)
    dtm_dense = dtm.todense()

    # 단어간 상관관계 구하기
    words_name = countervectorizer.get_feature_names_out()
    word_corr = np.corrcoef(dtm_dense, rowvar=0)
    word_edges = []
    for i in range(dtm_dense.shape[1]):
        for j in range(dtm_dense.shape[1]): # 단어의 개수: dtml_dense.shape[1]
            word_edges.append((words_name[i], words_name[j], word_corr[i, j]))

    # 연관 단어 튜플 생성
    related_words = []
    for word_edge in word_edges:
        if word_edge[0] == word_edge[1]:
            continue
        if word_edge[2] >= 0.4: # 0.4 이상이면 중간정도의 상관관계(연관의 기준으로 삼음)
            related_words.append((word_edge[0], word_edge[1]))

    # 단어*단어 행렬 만들기
    ttm = np.dot(dtm_dense.T, dtm_dense)
    
    # 그래프 만들기
    font_location = 'static/font/malgun.ttf'
    font_name = font_manager.FontProperties(fname=font_location).get_name()
    plt.rc('font', family=words_name)
    g = nx.Graph(ttm[:, :])
    en_map = dict(zip(g.nodes(), words_name))
    nx.draw(g, labels=en_map, with_labels=True, font_family=font_name)
    plt.savefig('static/img/graph.png')
    context = {
        'related_words': related_words,
    }
    return render(request, 'posts/related_words.html', context)