from django.shortcuts import render,redirect
from blog.models import UserInfo,Article,ArticleUpDown,Category,Tag,Article2Tag,Comment
from django.contrib import auth
from django.db.models import Count,Max,Min,F
from django.http import JsonResponse

# Create your views here.


def login(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        pwd = request.POST.get('pwd')
        user = auth.authenticate(username=user,password=pwd)
        if user:
            auth.login(request,user)
            return redirect('/head/')

    return render(request,'login.html')

def head(request):
    article_list = Article.objects.all()
    return render(request,'head.html',{'article_list':article_list})


def logout(request):
    auth.logout(request)
    return redirect('/head/')

from django.contrib.auth.decorators import login_required

def up(request):
    '''
    点赞需要参数  点赞人(request.user)  点赞文章ID   is_up 还是 is_down
    返回 是否点赞成功 新的赞数
    '''
    import json
    response = {'state': None, 'msg': None}
    is_up = json.loads(request.POST.get('is_up'))
    user = request.user
    article_id = int(request.POST.get('article_id'))
    print(666,article_id)

    article = Article.objects.filter(nid=article_id).first()
    article_updown = ArticleUpDown.objects.filter(user=user,article_id=article_id).first()

    if article_updown:

        response['state'] = False
        if article_updown.is_up:
            response['msg'] = '您已经推荐过了'
        else:
            response['msg'] = '您已经反对过了'
    else:
        article_updown = ArticleUpDown.objects.create(user=user, article_id=article_id,is_up = is_up)
        response['state'] = True
        if is_up:

            Article.objects.filter(nid=article_id).update(up_count=F('up_count') + 1)
            new_article=Article.objects.filter(nid=article_id).first()

            response['msg'] = new_article.up_count
        else:
             Article.objects.filter(nid=article_id).update(down_count=F('down_count') + 1)
             new_article = Article.objects.filter(nid=article_id).first()
             response['msg'] = new_article.down_count

    return JsonResponse(response)

@login_required
def comment(request):

    article_id=request.POST.get('article_id')
    pid = request.POST.get('pid')
    content = request.POST.get('content')
    comment = Comment.objects.create(article_id=article_id,user=request.user,parent_comment_id=pid,content=content)
    Article.objects.filter(pk=article_id).update(content_count=F("content_count") + 1)
    data={'status':True}
    data['timer']= comment.create_time
    data['content'] = comment.content
    data['user'] = request.user.username

    return JsonResponse(data)


@login_required
def backend(request):


    print(request.user)
    username = request.user.username

    user = UserInfo.objects.filter(username = username).first()
    article_list = Article.objects.filter(user = user)

    return render(request,'backend/backend.html',locals())

@login_required
def add_article(request):

    user = request.user
    if user.username:
        cate_list = Category.objects.filter(blog__userinfo=user)
        tags = Tag.objects.filter(blog__userinfo=user)




        if request.method == 'POST':

            title = request.POST.get('title')
            content = request.POST.get('content')
            tags_list = request.POST.get('tags')
            cate_pk = request.POST.get('cate')
            user = request.user.username
            user=UserInfo.objects.filter(username=user).first()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content,'html.parser',from_encoding='utf-8')
            for tag in soup.find_all():
                if tag.name in ['script',]:
                    tag.decompose()

            article_obj=Article.objects.create(title=title,content=content,desc=content[0:150],category_id=cate_pk,user=user)

            for tags_pk in tags_list:
                Article2Tag.objects.create(article_id=article_obj.pk,tag_id=tags_pk)

            return redirect("/backend/")



        return render(request,'backend/addtitle.html',locals())
    else:
        return render(request,'notfind.html')









def homesite(request,username,**kwargs):
    user = UserInfo.objects.filter(username=username).first()
    if user:
        # print('*************************',query_obj.values('article'))
        article_list = Article.objects.filter(user__username = username)
        blog = user.blog
        category_list = Category.objects.filter(blog=blog).annotate(c = Count('article__title')).values_list('title','c')
        tag_list = Tag.objects.filter(blog=blog).annotate(c = Count('article__title')).values_list('title','c')
        if kwargs:
            condition = kwargs.get('condition')
            params = kwargs.get('params')
            if condition == 'category':
                article_list=article_list.filter(category__title=params)

            if condition == 'tag':
                article_list = article_list.filter(tag__title=params)
            else:
                return render(request,'notfind.html')
        return render(request,'homesite.html',locals())
    return render(request,'notfind.html')

def article_detail(request,username,atc_id):
    user = UserInfo.objects.filter(username=username).first()
    if user:
        blog = user.blog
        category_list = Category.objects.filter(blog=blog).annotate(c = Count('article__title')).values_list('title','c')
        tag_list = Tag.objects.filter(blog=blog).annotate(c=Count('article__title')).values_list('title', 'c')
        article_detail=Article.objects.filter(nid=atc_id).first()
        comment_list = Comment.objects.filter(article__nid=atc_id)


        return render(request,'article_detail.html',locals())



def notfind(request):
    return render(request,'notfind.html')