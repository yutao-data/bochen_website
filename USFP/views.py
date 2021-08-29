import datetime
import math
import nltk
# nltk.download()
from django.core.paginator import *
from django.db import transaction
import json
import os
from PIL import Image
from django.http import *
from django.shortcuts import render, redirect
from django.urls import reverse
from nltk.corpus import stopwords
import jieba.analyse
from USFP.littleTools import *
from USFP.models import *
import jieba


# Create your views here.

def login(request, error):
    if request.method == "GET":
        if 'login' in request.COOKIES.keys():
            user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
            isAdmin=False
            if user.isVerified():
                if user.VerifiedUser.isAdmin:
                    isAdmin = True
            login = request.get_signed_cookie("login", salt="hello").split(',')
            commonUserID = login[0]
            commonUserPassword = login[1]
            return render(request, "View/login.html",
                          {"error": json.dumps(error), "commonUserID": commonUserID, "user": user,"isAdmin":isAdmin,
                           "commonUserPassword": commonUserPassword,
                           "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")})
        else:
            user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
            isAdmin=False
            if user.isVerified():
                if user.VerifiedUser.isAdmin:
                    isAdmin = True
            return render(request, "View/login.html", {"error": json.dumps(error),"user": user,"isAdmin":isAdmin,
                                                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                           "-tagShowNum")})
    commonUserPassword = request.POST.get("commonUserPassword", "")
    remind = request.POST.get("cookie", "")
    commonUserID = int(request.POST.get("commonUserID", ""))
    result = CommonUser.object.filter(commonUserID=commonUserID, commonUserPassword=commonUserPassword)
    if len(result) == 0:
        response = HttpResponseRedirect(reverse('USFP:login', args=(1,)))
        response.delete_cookie("login")
        return response
    request.session.set_expiry(3 * 60 * 60)
    request.session['commonUserID'] = commonUserID
    response = redirect("welcome")
    if remind == "1":
        response.set_signed_cookie('login', str(commonUserID) + "," + commonUserPassword,
                                   max_age=24 * 60 * 60 * 3, salt="hello")
    return response


def register(request):
    user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    if request.method == 'GET':
        return render(request, "View/register.html",
                      {"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum"), "user": user,"isAdmin":isAdmin})
    commonUserName = request.POST.get("commonUserName", "")
    commonUserPassword = request.POST.get("commonUserPassword", "")
    commonUserEmail = request.POST.get("commonUserEmail", "")
    areaIDList = Area.object.all()
    try:
        photo = request.FILES.get("photo", "")
        phototype = photo.name.split(".")[-1]
        try:
            photoName = str(CommonUser.objects.last().commonUserID + 1) + "." + phototype
        except:
            photoName = "1." + phototype
        photoLocation = os.path.join(".", ".", os.getcwd(), "media", "userImage", photoName)
        photo_resize = Image.open(photo)
        photo_resize.thumbnail((371, 475), Image.ANTIALIAS)
        photo_resize.save(photoLocation)
        user = CommonUser.objects.create(commonUserName=commonUserName, commonUserPassword=commonUserPassword,
                                         commonUserEmail=commonUserEmail, commonUserImage="userImage/" + photoName,
                                         area=Area.object.get(areaID=random.randint(1, len(areaIDList) + 1)))
    except Exception as e:
        print(e)
        user = CommonUser.objects.create(commonUserName=commonUserName, commonUserPassword=commonUserPassword,
                                         commonUserEmail=commonUserEmail,
                                         area=Area.object.get(areaID=random.randint(0, len(areaIDList) + 1)))
    if commonUserEmail.endswith('@mail.uic.edu.cn'):
        if request.POST.get('wantToBeAdmin', '') == 'wantToBeAdmin':
            VerifiedUser.objects.create(commonUser=user, isAdmin=True)
        else:
            VerifiedUser.objects.create(commonUser=user, isAdmin=False)
    return HttpResponseRedirect(reverse('USFP:suRegister'))


def suRegister(request):
    user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    return render(request, "View/suRegister.html",
                  {"commonUserID": CommonUser.objects.last().commonUserID, "user": user,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                       "-tagShowNum"),"isAdmin":isAdmin})


def forgetPassword(request):
    user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    if request.method == 'GET':
        return render(request, "View/forgetpwd.html",
                      {"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum"), "user": user,
                       "isAdmin":isAdmin})
    commonUserPassword = request.POST.get("commonUserPassword", "")
    commonUserID = request.POST.get("commonUserID", "")
    try:
        CommonUser.object.filter(commonUserID=int(commonUserID)).update(commonUserPassword=commonUserPassword)
        return redirect('USFP:suChangePwd')
    except Exception as e:
        return HttpResponse("Fail")


def suChangePwd(request):
    user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    return render(request, "View/suChangePwd.html",
                  {"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum"), "user": user,
                   "isAdmin":isAdmin})


@transaction.atomic
def submitSuggestion(request):
    if request.method == 'GET':
        commonUserID = request.session.get("commonUserID", 5)
        commonUser = CommonUser.object.get(commonUserID=commonUserID)
        return render(request, "View/submitSuggestion.html", {'user': commonUser,
                                                              "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                                  "-tagShowNum")})
    save_tag = transaction.savepoint()
    try:
        commonUserID = request.session.get("commonUserID", 5)
        commonUser = CommonUser.object.get(commonUserID=commonUserID)
        suggestion = request.POST.get("suggestionContent")
        suggestionObject = Suggestion.objects.create(content=suggestion, commonUser=commonUser)
        allTagsList = Tag.objects.values_list("tagName", flat=True)
        isAdmin = False
        if commonUser.isVerified():
            if commonUser.VerifiedUser.isAdmin:
                isAdmin = True
        suggestionObject.save()
        if check_contain_chinese(suggestion):
            for i in jieba.analyse.extract_tags(suggestion, topK=5, withWeight=True, allowPOS=('n', 'nr', 'ns')):
                if i[0] in allTagsList:
                    tag = Tag.objects.get(tagName=i[0])
                    suggestionObject.tags.add(tag)
                    tag.tagShowNum = tag.tagShowNum + 1
                    tag.save()
                else:
                    newTag = Tag.objects.create(tagName=i[0], tagShowNum=1)
                    suggestionObject.tags.add(newTag)
                    allTagsList = Tag.objects.values_list("tagName", flat=True)
        else:
            suggestionCuttedList = " ".join(jieba.cut_for_search(suggestion))
            for i in nltk.pos_tag(nltk.word_tokenize(suggestionCuttedList)):
                if i[1].startswith('N'):
                    if i[0].lower() in allTagsList and i[0] not in stopwords.words('english'):
                        tag = Tag.objects.get(tagName=i[0].lower())
                        suggestionObject.tags.add(tag)
                        tag.tagShowNum = tag.tagShowNum + 1
                        tag.save()
                    else:
                        newTag = Tag.objects.create(tagName=i[0].lower(), tagShowNum=1)
                        suggestionObject.tags.add(newTag)
                        allTagsList = Tag.objects.values_list("tagName", flat=True)
        suggestionObject.save()
        return render(request, "View/submitSuggestionResult.html",
                      {"state": 1, "suggestionID": suggestionObject.suggestionID, 'user': commonUser,"isAdmin":isAdmin,
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")})
    except Exception as e:
        print(e)
        transaction.savepoint_rollback(save_tag)
        return render(request, "View/submitSuggestionResult.html", {"state": 0, 'user': commonUser,"isAdmin":isAdmin,
                                                                    "allTags": Tag.objects.filter(
                                                                        tagShowNum__gt=0).order_by("-tagShowNum")})


def searchSuggestion(request):
    try:
        suggestionID = int(request.POST.get("searchSuggestionID", ""))
        commonUser = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
        suggestion = Suggestion.object.get(suggestionID=suggestionID)
        assert not suggestion.isDelete
        isAdmin = False
        if commonUser.isVerified():
            if commonUser.VerifiedUser.isAdmin:
                isAdmin = True
        if commonUser.isVerified():
            if suggestion.commonUser.area in commonUser.VerifiedUser.adminArea.all():
                return HttpResponseRedirect(reverse("USFP:adminViewOneSuggestion", args=(suggestionID, 1)))
        return render(request, "View/searchSuggestion.html", {"suggestion": suggestion, "isAuthor": (
                suggestion.commonUser.commonUserID == commonUser.commonUserID),
                                                              'user': commonUser,
                                                              "isAdmin":isAdmin,
                                                              "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                                  "-tagShowNum")})
    except Exception as e:
        print(e)
        return redirect("welcome")


def viewTag(request, tagID, num):
    tag = Tag.objects.get(tagID=tagID)
    suggestions = tag.Suggestion.filter(visible=True).order_by("postTime")
    user = CommonUser.objects.get(commonUserID=request.session.get("commonUserID", 5))
    if int(num) < 1:
        num = 1
    else:
        num = int(num)
    suggestionPager = Paginator(suggestions, 10)
    try:
        suggestionPrepageData = suggestionPager.page(num)
    except EmptyPage:
        suggestionPrepageData = suggestionPager.page(suggestionPager.num_pages)
    begin = (num - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > suggestionPager.num_pages:
        end = suggestionPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    suggestionPageList = range(begin, end + 1)
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    return render(request, "View/viewTag.html",
                  {"suggestionPager": suggestionPager, 'suggestionPrepageData': suggestionPrepageData,
                   "suggestionPageList": suggestionPageList, "user": user, "isAdmin": isAdmin,
                   "tag": tag, "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})


def viewAllTags(request, num):
    user = CommonUser.objects.get(commonUserID=request.session.get("commonUserID", 5))
    tags = Tag.objects.order_by("tagName")
    if int(num) < 1:
        num = 1
    else:
        num = int(num)
    tagsPager = Paginator(tags, 10)
    try:
        tagsPrepageData = tagsPager.page(num)
    except EmptyPage:
        tagsPrepageData = tagsPager.page(tagsPager.num_pages)
    begin = (num - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > tagsPager.num_pages:
        end = tagsPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    tagsPageList = range(begin, end + 1)
    isAdmin = False
    if user.isVerified():
        if user.VerifiedUser.isAdmin:
            isAdmin = True
    return render(request, "View/viewAllTags.html",
                  {"tagsPager": tagsPager, 'tagsPrepageData': tagsPrepageData,
                   "tagsPageList": tagsPageList, "user": user, "isAdmin": isAdmin,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
