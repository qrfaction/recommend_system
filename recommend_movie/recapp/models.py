from django.db import models
from django.contrib.auth.models import User
import numpy as np
import json

class JSONField(models.TextField):
    description = "Json"
    def to_python(self, value):
        v = models.TextField.to_python(self, value)
        try:
            return json.loads(v)
        except:
            print(v,type(v),'------------------------')
            pass
        return v
    def get_prep_value(self, value):
        return json.dumps(value)
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    array =JSONField()                           #存储电影打分数据
    arrayratedmoviesindxs = JSONField()   #看过的电影索引
    name = models.CharField(max_length=1000)
    lastrecs =JSONField()           #最近推荐的电影

    def __str__(self):
        return self.user.name

    def save(self, *args, **kwargs):
        create = kwargs.pop('create', None)   #第二个参数是指如果没找到返回None
        recsvec = kwargs.pop('recsvec', None)
        print('create:', create)
        if create == True:
            super(UserProfile, self).save(*args, **kwargs)
        elif recsvec is not None:
            if type(recsvec)!=list:
                self.lastrecs =recsvec.tolist()
            else:
                self.lastrecs = recsvec
            super(UserProfile, self).save(*args, **kwargs)
        else:
            nmovies = MovieData.objects.count() #objects必定存在
            array = np.zeros(nmovies)
            ratedmovies = self.ratedmovies.all()
            #用户看过电影的索引
            self.arrayratedmoviesindxs = [m.movieindx for m in ratedmovies]
            for m in ratedmovies:
                array[m.movieindx] = m.value
            self.array =list(array)
            super(UserProfile, self).save(*args, **kwargs)


class MovieRated(models.Model):#记录对应用户为哪些电影打过分
    #将userprofile设置为外键   userprofile中会出现ratemovies关联movierated
    user = models.ForeignKey(UserProfile, related_name='ratedmovies')
    movie = models.CharField(max_length=100)
    movieindx = models.IntegerField(default=-1)#该电影在电影列表中的索引
    value = models.IntegerField()   #用户打的分数

    def __str__(self):
        return self.movie

class MovieData(models.Model):
    title = models.CharField(max_length=100)  #影片名
    array = JSONField()                        #向量表示 电影简介的tf-idf
    ndim = models.IntegerField(default=300)   #维度
    description = models.TextField()         #简介
