import os
from datetime import datetime

import numpy as np
from PIL import Image
from bokeh.transform import factor_cmap
from django.http import HttpResponse
from django.shortcuts import render
from matplotlib import pyplot as plt
from bokeh.io import show, output_file, save
from bokeh.plotting import figure
import bokeh.palettes as bp
from USFP.littleTools import *
from USFP.models import *
import wordcloud


def welcome(request, logout=0):
    if logout:
        request.session.clear()
        user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
        return render(request, 'View/welcome.html',
                      {"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11],
                       'user': user, 'isAdmin': False, })
    try:
        user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
        if user.VerifiedUser.isAdmin:
            return render(request, 'View/welcome.html', {'user': user, 'isAdmin': True,
                                                         "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                             "-tagShowNum")[1:11]})
        else:
            return render(request, 'View/welcome.html', {'user': user, 'isAdmin': False,
                                                         "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                             "-tagShowNum")[1:11]})
    except Exception:
        return render(request, 'View/welcome.html', {'user': user, 'isAdmin': False,
                                                     "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                         "-tagShowNum")[1:11]})


def getUserKey(request):
    try:
        commonUserID = request.POST.get('commonUserID', "")
        to_add = CommonUser.object.get(commonUserID=int(commonUserID)).commonUserEmail
        key = sendEmail(to_add)
        return HttpResponse(key)
    except Exception as e:
        return HttpResponse(1)


def getAdKey(request):
    try:
        return HttpResponse(sendAdKey())
    except:
        return HttpResponse(1)


def sendCheckKey(request):
    try:
        emailAdd = request.POST.get('emailAdd', "")
        print(emailAdd)
        key = sendEmail(emailAdd)
        return HttpResponse(key)
    except:
        return HttpResponse(1)


def refreshDB(request):
    try:
        assert request.session['commonUserID'] == 1
        assert request.method == "POST"
    except Exception as e:
        print(e)
        return HttpResponse("Fail")
    userList = CommonUser.objects.filter(isDelete=True)
    areaList = Area.objects.filter(isDelete=True)
    suggestionList = Suggestion.objects.filter(isDelete=True)
    deleteList = [userList, areaList, suggestionList]
    nowDate = datetime.now()
    for i in suggestionList:
        if i.isReplied:
            for j in i.ReplySuggestion.all():
                j.delete()
    for i in deleteList:
        for j in i:
            try:
                if ((nowDate - j.deleteDate).days > 14):
                    j.delete()
            except Exception as e:
                print(e)
    return HttpResponse("Success")


def refreshGraph(request):
    try:
        assert request.session['commonUserID'] == 1
        assert request.method == "POST"
        tagAndNUmList = list(Tag.objects.order_by("-tagShowNum")[1:40].values_list("tagName", "tagShowNum"))
        tadAndNumDict = {}
        for i in tagAndNUmList:
            tadAndNumDict[i[0]] = i[1]
        webImageLocation = os.path.join(".", ".", os.getcwd(), "media", "webImage")
        mask = np.array(Image.open(os.path.join(webImageLocation, "cat.PNG")))
        wc = wordcloud.WordCloud(
            font_path=os.path.join(webImageLocation, "simsun.ttf"),
            mask=mask,
            max_words=40,
            max_font_size=100,
            background_color='white'
        )
        wc.generate_from_frequencies(tadAndNumDict)
        image_colors = wordcloud.ImageColorGenerator(mask)
        wc.recolor(color_func=image_colors)
        if os.path.isfile(os.path.join(webImageLocation, "WordCloud.PNG")):
            os.remove(os.path.join(webImageLocation, "WordCloud.PNG"))
        plt.imshow(wc)
        plt.axis('off')
        plt.savefig(os.path.join(webImageLocation, "WordCloud.PNG"))

        tagsList = list(Tag.objects.order_by("-tagShowNum")[1:11].values_list("tagName", flat=True))
        tagsShowNumList = list(Tag.objects.order_by("-tagShowNum")[1:11].values_list("tagShowNum", flat=True))
        p = figure(x_range=tagsList, plot_height=300, title="Tag Counts", tooltips="top: @top",
                   toolbar_location="above",
                   tools="pan,wheel_zoom,save,reset,undo,redo")
        p.vbar(x=tagsList, top=tagsShowNumList, width=0.9,
               fill_color=bp.Blues[256][50:220:17], )
        p.xgrid.grid_line_color = None
        if os.path.isfile(os.path.join(webImageLocation, "Bar.html")):
            os.remove(os.path.join(webImageLocation, "Bar.html"))
        path = os.path.join(webImageLocation, "Bar.html")
        output_file(path)
        save(obj=p, filename=path, title="output")

        return HttpResponse("Success!")
    except Exception as e:
        print(e)
        return HttpResponse("Fail")


def page_not_found(request, exception):
    user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    return render(request, 'Error/404.html',
                  {"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11],"user":user,
                   "isAdmin":isAdmin})


def startScrapy(request):
    # try:
    #     assert request.session['commonUserID']== 1
    #     assert request.method=="POST"
    # except Exception as e:
    #     print(e)
    #     return HttpResponse("Fail")
    # os.system('cd ZhiHuScrapy;scrapy crawl ZhiHuScrapy')
    return HttpResponse("Done")
