import datetime
import json
import math
import os
from nltk.corpus import stopwords
import jieba
import nltk
from PIL import Image
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction
from django.http import *
from django.shortcuts import render, redirect
from django.urls import reverse
from USFP.models import *
from .littleTools import check_contain_chinese
import jieba.analyse


def userInfor(request):
    user = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
    if user.isVerified():
        return render(request, "CommonUser/userInfor.html",
                      {"user": user, 'verified': 1,
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
    else:
        return render(request, "CommonUser/userInfor.html",
                      {"user": user, 'verified': 0,
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})


def userChange(request, changeType):
    user = CommonUser.object.get(commonUserID=request.session.get('commonUserID',5))
    try:
        isAdmin = user.VerifiedUser.isAdmin
    except:
        isAdmin = False
    if request.method == 'GET':
        if changeType == "EmailAdd" or changeType == "Password":
            return render(request, "CommonUser/userChangeInfor.html",
                          {"changeType_js": json.dumps(changeType), "changeType_py": changeType,"isAdmin":isAdmin,
                           "user":user,
                           "commonUserID": request.session['commonUserID'],
                           "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
        if changeType == "Image" or changeType == "Name":
            return render(request, "CommonUser/userChangeInfor.html",
                          {"changeType_js": json.dumps(changeType), "changeType_py": changeType,"isAdmin":isAdmin,"user":user,
                           "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
    if changeType == "EmailAdd":
        newEmailAdd = request.POST.get("newEmailAdd", "")
        user.commonUserEmail=newEmailAdd
        if newEmailAdd.endswith('@mail.uic.edu.cn') and user.isVerified():
            verified = user.VerifiedUser
            if request.POST.get('wantToBeAdmin', '') == 'wantToBeAdmin':
                verified.isAdmin = True
                verified.save()
        elif newEmailAdd.endswith('@mail.uic.edu.cn'):
            if request.POST.get('wantToBeAdmin', '') == 'wantToBeAdmin':
                VerifiedUser.objects.create(isAdmin=True, commonUser=user)
            else:
                VerifiedUser.objects.create(commonUser=user)
        else:
            user.VerifiedUser.delete()
    if changeType == "Image":
        photo = request.FILES.get("photo", "")
        photoName = str(request.session['commonUserID']) + "." + photo.name.split(".")[1]
        photo_resize = Image.open(photo)
        photo_resize.thumbnail((371, 475), Image.ANTIALIAS)
        if os.path.isfile(os.path.join(".", ".", os.getcwd(), "media", str(user.commonUserImage))):
            os.remove(os.path.join(".", ".", os.getcwd(), "media", str(user.commonUserImage)))
        photo_resize.save(os.path.join(".", ".", os.getcwd(), "media", "userImage", photoName))
        user.commonUserImage="userImage/" + photoName
    if changeType == "Name":
        newName = request.POST.get("newName", "")
        user.commonUserName=newName
    if changeType == "Password":
        newPassword = request.POST.get("password", "")
        user.commonUserPassword=newPassword
    user.save()
    return HttpResponseRedirect(reverse("USFP:userSuChange", args=(changeType,)))


def userSuChange(request, changeType):
    user = CommonUser.object.get(commonUserID=request.session.get('commonUserID',5))
    try:
        isAdmin = user.VerifiedUser.isAdmin
    except:
        isAdmin = False
    return render(request, "CommonUser/userSuChange.html", {"changeType": changeType,"isAdmin":isAdmin,"user":user,
                                                            "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                                "-tagShowNum")[1:11]})


def userViewSuggestions(request, num):
    try:
        user = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    try:
        isAdmin = user.VerifiedUser.isAdmin
    except:
        isAdmin = False
    suggestions = user.Suggestion.filter(visible=True).order_by("postTime")
    if int(num) < 1:
        suggestionNum = 1
    else:
        suggestionNum = int(num)
    suggestionPager = Paginator(suggestions, 10)
    try:
        suggestionPrepageData = suggestionPager.page(suggestionNum)
    except EmptyPage:
        suggestionPrepageData = suggestionPager.page(suggestionPager.num_pages)
    begin = (suggestionNum - int(math.ceil(10.0 / 2)))
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
    try:
        isAdmin = user.VerifiedUser.isAdmin
    except:
        isAdmin = False
    return render(request, "CommonUser/userViewSuggestions.html",
                  {"suggestionPager": suggestionPager, 'suggestionPrepageData': suggestionPrepageData,
                   "suggestionPageList": suggestionPageList, "user": user, "isAdmin": isAdmin,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})


def userDeleteSuggestions(request):
    if request.method == 'GET':
        return HttpResponse('Fail')
    deleteList = [i for i in request.POST.get("listToDelete").split("-") if len(i) != 0]
    user = CommonUser.object.get(commonUserID=request.session['commonUserID'])
    try:
        for i in deleteList:
            suggestionToDelete = Suggestion.object.get(suggestionID=int(i))
            suggestionToDelete.visible = False
            suggestionToDelete.save()
    except Exception as e:
        print(e)
        return HttpResponse("Fail")
    return HttpResponse("Success")


def userViewOneSuggestion(request, suggestionID, num):
    try:
        user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
        try:
            isAdmin = user.VerifiedUser.isAdmin
        except:
            isAdmin = False
        suggestion = Suggestion.object.get(suggestionID=suggestionID)
        if user.isVerified():
            if suggestion.commonUser.area in user.VerifiedUser.adminArea.all():
                return HttpResponseRedirect(reverse("USFP:adminViewOneSuggestion", args=(suggestionID, 1)))
        if suggestion.isReplied():
            replySuggestionList = suggestion.ReplySuggestion.filter(selfSuggestion__isDelete=False,
                                                                    selfSuggestion__visible=True).order_by(
                "selfSuggestion__postTime")
        else:
            replySuggestionList = []
        if int(num) < 1:
            replyNum = 1
        else:
            replyNum = int(num)
        replySuggestionPager = Paginator(replySuggestionList, 10)
        try:
            replySuggestionPrepageData = replySuggestionPager.page(replyNum)
        except EmptyPage:
            replySuggestionPrepageData = replySuggestionPager.page(replySuggestionPager.num_pages)
        begin = (replyNum - int(math.ceil(10.0 / 2)))
        if begin < 1:
            begin = 1
        end = begin + 9
        if end > replySuggestionPager.num_pages:
            end = replySuggestionPager.num_pages
        if end <= 10:
            begin = 1
        else:
            begin = end - 9
        replySuggestionPageList = range(begin, end + 1)
        return render(request, "CommonUser/userViewOneSuggestion.html", {"suggestion": suggestion,
                                                                         "isAuthor": (
                                                                                 suggestion.commonUser.commonUserID == user.commonUserID),
                                                                         'user': user, 'isVerified': user.isVerified(),
                                                                         "isAdmin":isAdmin,
                                                                         'replySuggestionPrepageData': replySuggestionPrepageData,
                                                                         'replySuggestionPageList': replySuggestionPageList,
                                                                         "suggestion_tags": suggestion.tags.all(),
                                                                         "allTags": Tag.objects.filter(
                                                                             tagShowNum__gt=0).order_by("-tagShowNum")[
                                                                                    1:11]})
    except Exception as e:
        print(e)
        return redirect("welcome")


@transaction.atomic
def userChangeSuggestion(request, suggestionID):
    user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
    try:
        isAdmin = user.VerifiedUser.isAdmin
    except:
        isAdmin = False
    if request.method == "GET":
        return render(request, "CommonUser/userChangeSuggestion.html", {'suggestionID': suggestionID, 'user': user,
                                                                        "isAdmin":isAdmin})
    suggestion = Suggestion.object.get(suggestionID=suggestionID)
    save_tag = transaction.savepoint()
    try:
        for i in suggestion.tags.all():
            i.tagShowNum = i.tagShowNum - 1
            suggestion.tags.remove(i)
            i.save()
        newContent = request.POST.get("newSuggestionContent")
        allTagsList = Tag.objects.values_list("tagName", flat=True)
        suggestion.content = newContent
        if check_contain_chinese(newContent):
            for i in jieba.analyse.extract_tags(newContent, topK=5, withWeight=True, allowPOS=('n', 'nr', 'ns')):
                if i[0] in allTagsList and i[0] not in stopwords.words('english'):
                    tag = Tag.objects.get(tagName=i[0])
                    suggestion.tags.add(tag)
                    tag.tagShowNum = tag.tagShowNum + 1
                    tag.save()
                else:
                    newTag = Tag.objects.create(tagName=i[0], tagShowNum=1)
                    suggestion.tags.add(newTag)
                    allTagsList = Tag.objects.values_list("tagName", flat=True)
        else:
            suggestionCuttedList = " ".join(jieba.cut_for_search(newContent))
            for i in nltk.pos_tag(nltk.word_tokenize(suggestionCuttedList)):
                if i[1].startswith('N'):
                    if i[0].lower() in allTagsList and i[0] not in stopwords.words('english'):
                        tag = Tag.objects.get(tagName=i[0].lower())
                        suggestion.tags.add(tag)
                        tag.tagShowNum = tag.tagShowNum + 1
                        tag.save()
                    else:
                        newTag = Tag.objects.create(tagName=i[0].lower(), tagShowNum=1)
                        suggestion.tags.add(newTag)
                        allTagsList = Tag.objects.values_list("tagName", flat=True)
        suggestion.save()
        if not user.isVerified() or not suggestion.isReplied():
            suggestion.visible = False
        try:
            ReplySuggestion.objects.get(selfSuggestion=suggestion)
            suggestion.visible = True
        except:
            pass
        suggestion.save()
        return render(request, "CommonUser/userSuChangeSuggestion.html", {'suggestionID': suggestion.suggestionID,
                                                                          "allTags": Tag.objects.filter(
                                                                              tagShowNum__gt=0).order_by("-tagShowNum")[
                                                                                     1:11],'user': user,
                                                                        "isAdmin":isAdmin})
    except Exception as e:
        print(e)
        transaction.savepoint_rollback(save_tag)
        return redirect("welcome")


def userSubmitComment(request, suggestionID):
    try:
        content = request.POST.get("replySuggestionContent")
        user = CommonUser.object.get(commonUserID=request.session.get("commonUserID", 5))
        newComment = Suggestion.objects.create(content=content, commonUser=user, visible=True)
        ReplySuggestion.objects.create(selfSuggestion=newComment,
                                       suggestionToReply=Suggestion.objects.get(suggestionID=suggestionID))
        return HttpResponseRedirect(reverse("USFP:userViewOneSuggestion", args=(suggestionID, 1)))
    except Exception as e:
        print(e)
        return redirect("welcome")
