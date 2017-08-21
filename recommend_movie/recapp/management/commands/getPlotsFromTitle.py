from django.core.management.base import BaseCommand
import numpy as np
import json
import pandas as pd
import requests

# python  manage.py get_plotsfromtitles
# --input=/Users/andrea/Desktop/book_packt/chapters/5/data/utilitymatrix.csv
# --outputplots=plots.csv --outputumatrix='umatrix.csv'
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--input',
                            action='store',
                            dest='umatrixfile',  #在函数中获取的命令行参数的键值对的键名  如option["umatrixfile"]
                            ype=str,
                            help='Input utility matrix')
        parser.add_argument('--outputplots',
                            action='store',
                            dest='plotsfile',  # 在函数中获取的命令行参数的键值对的键名  如option["umatrixfile"]
                            type=str,
                            help='output file')
        parser.add_argument('--outputumatrix',
                            action='store',
                            dest='umatrixoutfile',  # 在函数中获取的命令行参数的键值对的键名  如option["umatrixfile"]
                            type=str,
                            help='output file')

    def getPlotFromOmdb(self, col, df_moviesplots, df_movies, df_utilitymatrix): #获取简介

        #utility 效用  omdb  open movie database 开放电影数据库
        string = col.split(';')[0]

        title = string[:-6].strip()
        year = string[-5:-1]
        # plot = ' '.join(title.split(' ')).encode('ascii', 'ignore') + '. '
        plot = title + '. '

        "还得添加api"
        url = "http://www.omdbapi.com/?apikey=[yourkey]t=" + title + "&y=" + year + "&plot=full&r=json"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers)
        jsondata = json.loads(r.content)
        if 'Plot' in jsondata:  #若该电影有简介
            # store plot + title
            plot += jsondata['Plot']

        if plot != None and plot != '' and plot != np.nan and len(plot) > 3:  # at least 3 letters to consider the movie
            df_moviesplots.loc[len(df_moviesplots)] = [string, plot]  #在电影简介矩阵中最后一行添加数据
            df_utilitymatrix[col] = df_movies[col]
            print(len(df_utilitymatrix.columns))

        return df_moviesplots, df_utilitymatrix

    def handle(self, *args, **options):
        print(1111111111111111111111111111111111)
        pathutilitymatrix = options['umatrixfile']    #效用矩阵存储路径
        df_movies = pd.read_csv(pathutilitymatrix)
        movieslist = list(df_movies.columns[1:])  #0列是用户列

        df_moviesplots = pd.DataFrame(columns=['title', 'plot'])
        df_utilitymatrix = pd.DataFrame()
        df_utilitymatrix['user'] = df_movies['user']

        print('nmovies:', len(movieslist))
        for m in movieslist:
            df_moviesplots, df_utilitymatrix = self.getPlotFromOmdb(m, df_moviesplots, df_movies, df_utilitymatrix)

        print(len(df_movies.columns), '--', len(df_utilitymatrix.columns))
        outputfile = options['plotsfile']
        df_moviesplots.to_csv(outputfile, index=False)
        outumatrixfile = options['umatrixoutfile']
        df_utilitymatrix.to_csv(outumatrixfile, index=False)
