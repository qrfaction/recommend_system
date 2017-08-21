from .models import MovieData,MovieRated,UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer
from django.shortcuts import render
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.core.cache import cache
from urllib import parse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer
import pandas as pd
from .management.commands import load_data
from sklearn.metrics.pairwise import cosine_similarity
import json
from .management.commands.load_data import CF_itembased,LogLikelihood

umatrixpath = '/Users/andrea/Desktop/book_packt/chapters/7/server_movierecsys/umatrix.csv'
tknzr = WordPunctTokenizer()

stoplist = stopwords.words('english')
stemmer = PorterStemmer()
nmoviesperquery=5
nminimumrates=5
recmethod = 'loglikelihood' #推荐算法默认使用对数似然比
numrecs=5

def home(request):
    def PreprocessTfidf(texts, stoplist=[], stem=False):
        newtexts = []
        for text in texts:
            if stem:
                tmp = [w for w in tknzr.tokenize(text) if w not in stoplist]
            else:
                tmp = [stemmer.stem(w) for w in [w for w in tknzr.tokenize(text) if w not in stoplist]]
            newtexts.append(' '.join(tmp))
        return newtexts

    context = {}
    if request.method == 'POST':
        post_data = request.POST
        data = post_data.get('data', None)
        if data:
            '''reverse函数的第一个参数是urls.py中url的name，
                        args将对应的变量填入该url模板
                        并返回生成的url字符串'''
            return redirect('%s?%s' % (reverse('recapp:home'),
                                       parse.urlencode({'q': data})))
    elif request.method == 'GET':
        get_data = request.GET
        data = get_data.get('q', None)
        titles = cache.get('titles')
        if titles == None:
            print('load data...')
            texts = []
            mobjs = MovieData.objects.all()
            ndim = mobjs[0].ndim
            matr = np.empty([1, ndim])
            titles_list = []
            cnt = 0
            for obj in mobjs:
                texts.append(obj.description)
                newrow = np.array(obj.array)
                # print 'enw:',newrow
                if cnt == 0:
                    matr[0] = json.loads(newrow)
                else:
                    matr = np.vstack([matr, newrow])
                titles_list.append(obj.title)
                cnt += 1
            vectorizer = TfidfVectorizer(min_df=1, max_features=ndim)
            processedtexts = PreprocessTfidf(texts, stoplist, True)
            model = vectorizer.fit(processedtexts)
            cache.set('model', model)
            cache.set('data', matr)
            cache.set('titles', titles_list)
        else:
            print('loaded', str(len(titles)))

        Umatrix = cache.get('umatrix')
        if Umatrix is None:
            df_umatrix = pd.read_csv(umatrixpath)
            Umatrix = df_umatrix.values[:, 1:]
            print('umatrix:', Umatrix.shape)
            cache.set('umatrix', Umatrix)
            cf_itembased = load_data.CF_itembased(Umatrix)
            cache.set('cf_itembased', cf_itembased)
            cache.set('loglikelihood', load_data.LogLikelihood(Umatrix,
                            df_umatrix.columns[1:]))

        if not data:
            return  render(request,
                   'templates/home.html',context)
        # load all movies vectors/titles
        matr = cache.get('data')
        print('matr', len(matr))
        titles = cache.get('titles')
        print('ntitles:', len(titles))
        model_tfidf = cache.get('model')

        # load in cache rec sys methods
        print('load methods...')

        # find movies similar to the query
        # print 'names:',len(model_tfidf.get_feature_names())
        queryvec = model_tfidf.transform([data.lower()]).toarray()

        # 行矩阵化行向量
        sims = cosine_similarity(queryvec, matr)[0]
        indxs_sims = list(sims.argsort()[::-1])

        titles_query = list(np.array(titles)[indxs_sims][:nmoviesperquery])

        #python3中zip函数会返回zip对象 需得把他变成list
        context['movies'] = list(zip(titles_query, indxs_sims[:nmoviesperquery]))

        context['rates'] = [1, 2, 3, 4, 5]
        return render(request,
                      'templates/query_results.html', context)


def auth(request):
    print("111111111111111111111111111111111111111")
    if request.method == 'GET':
        data = request.GET
        auth_method = data.get('auth_method')
        if auth_method=='sign in':
            return render(request,
                          'templates/signin.html',{})
        else:
            return render(request,
                          'templates/createuser.html',{})
    elif request.method == 'POST':
        post_data = request.POST
        name = post_data.get('name', None)
        pwd = post_data.get('pwd', None)
        pwd1 = post_data.get('pwd1', None)
        print('auth:',request.user.is_authenticated())
        create = post_data.get('create', None)#hidden input
        if name and pwd and create:
            #用户已存在或者注册时两次密码输入不一致
            if User.objects.filter(username=name).exists() or pwd!=pwd1:
                return render(request,
                      'templates/userexistsorproblem.html', {})
            #创建用户 并存入数据库
            user = User.objects.create_user(username=name,password=pwd)

            uprofile = UserProfile()
            uprofile.user = user
            uprofile.name = user.username
            uprofile.save(create=True)
            user = authenticate(username=name, password=pwd)
            login(request, user) #登陆后request会存储当前用户的user方便以后用于验证
            return render(request,
                         'templates/home.html', {})
        elif name and pwd:
            user = authenticate(username=name, password=pwd)
            if user:
                login(request, user)
                return render(request,
                              'templates/home.html', {})
            else:
                #notfound
                return render(request,
                              'templates/nopersonfound.html', {})

def signout(request):
    logout(request)
    return render(request,
        'templates/home.html',{})


def rate_movie(request):
    def RemoveFromList(liststrings, string):
        outlist = []
        for s in liststrings:
            if s == string:
                continue
            outlist.append(s)
        return outlist
    data = request.GET
    rate = data.get("vote")  #用户打的分
    print(request.user.is_authenticated())
    # movies, moviesindxs = zip(*literal_eval(data.get("movies")))
    movies, moviesindxs = zip(*eval(data.get("movies")))
    movie = data.get("movie")
    movieindx = int(data.get("movieindx"))
    # save movie rate

    if request.user.is_superuser:
        return render(request,
                      'templates/superusersignin.html', {})
    elif request.user.is_authenticated():
        userprofile = UserProfile.objects.get(user=request.user)
    else:
        return render(request,
                      'templates/pleasesignin.html', {})

    #更新分数
    if MovieRated.objects.filter(movie=movie).filter(user=userprofile).exists():
        mr = MovieRated.objects.get(movie=movie, user=userprofile)
        mr.value = int(rate)
        mr.save()
    #创建分数
    else:
        mr = MovieRated()
        mr.user = userprofile
        mr.value = int(rate)
        mr.movie = movie
        mr.movieindx = movieindx
        mr.save()

    userprofile.save()
    # get back the remaining movies
    movies = RemoveFromList(movies, movie)
    moviesindxs = RemoveFromList(moviesindxs, movieindx)
    print(movies)
    context = {}
    context["movies"] = list(zip(movies, moviesindxs))
    context["rates"] = [1, 2, 3, 4, 5]
    return render(request,
     'templates/query_results.html', context)


def movies_recs(request):
    print('uuuu:', request.user.is_superuser)
    if request.user.is_superuser:
        return render(request,
                      'templates/superusersignin.html',{})
    elif request.user.is_authenticated():
        userprofile = UserProfile.objects.get(user=request.user)
    else:
        return render(request,
                      'templates/pleasesignin.html', {})
    ratedmovies = userprofile.ratedmovies.all()
    print('rated:', ratedmovies, '--', [r.movieindx for r in ratedmovies])
    context = {}
    #用户看过的电影太少 不予推荐
    if len(ratedmovies) < nminimumrates:
        context['nrates'] = len(ratedmovies)
        context['nminimumrates'] = nminimumrates
        return render(request,
                      'templates/underminimum.html', context)

    #不知道为啥取出来是字符串 先暂时这么处理吧
    u_vec = np.array(json.loads(userprofile.array))
    #取出之前计算完的效用矩阵与电影
    Umatrix = cache.get('umatrix')
    movieslist = cache.get('titles')
    # recommendation...
    u_rec=np.copy(u_vec)
    if recmethod == 'cf_itembased':
        cf_itembased = cache.get('cf_itembased')
        if cf_itembased == None:
            cf_itembased = CF_itembased(Umatrix)
        #基于商品的协同过滤补全副本用户向量u_rec非u_vec
        u_rec = cf_itembased.CalcRatings(u_vec, numrecs)

    elif recmethod == 'loglikelihood':
        llr = cache.get('loglikelihood')
        if llr is None:
            llr = LogLikelihood(Umatrix, movieslist)
        print(u_rec)
        u_rec = llr.GetRecItems(u_vec, True)

    # save last recs
    userprofile.save(recsvec=u_rec)
    context['recs'] = list(np.array(movieslist)[list(u_rec)][:numrecs])
    return render(request,
                  'templates/recommendations.html', context)