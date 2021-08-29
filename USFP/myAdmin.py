import json
import math
import os
from PIL import Image
from django.core.paginator import *
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from datetime import *


def adminInfor(request):
    try:
        admin = CommonUser.objects.get(commonUserID=request.session["commonUserID"])
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    adminArea = admin.VerifiedUser.adminArea.filter(isDelete=False)
    if request.method == "GET":
        return render(request, "Admin/adminInfor.html",
                      {"admin": admin, "areaSet": adminArea, "user": admin,"isAdmin":True,
                       "areaIDs_js": json.dumps(list(adminArea.values("areaID"))),
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
    else:
        for i in adminArea:
            try:
                if request.POST.get("deleteArea" + str(i.areaID), "0") == "1":
                    i.isDelete = True
                    i.deleteDate = datetime.now()
                    operation = AreaOperation(verifiedUser=admin.VerifiedUser, area=i, operationType="deleteArea",
                                              content="Delete the area")
                    operation.save()
                    i.save()
                if request.POST.get("updataAreaName" + str(i.areaID), "0") == "1":
                    originalName = i.areaName
                    i.areaName = request.POST.get("newAreaName" + str(i.areaID))
                    operation = AreaOperation(verifiedUser=admin.VerifiedUser, operationType="updateArea", area=i,
                                              content="Origin Name:" + originalName + " " + "New Name:" + request.POST.get(
                                                  "newAreaName" + str(i.areaID)))
                    operation.save()
                    i.save()
            except Exception as e:
                print(e)
        return HttpResponseRedirect(reverse("USFP:adminInfor"))


def adminChangeInfor(request, changeType):
    if request.method == 'GET':
        admin = CommonUser.object.get(commonUserID=request.session["commonUserID"])
        if changeType == "Email" or changeType == "Password":
            return render(request, "Admin/adminChangeInfor.html",
                          {"changeType_js": json.dumps(changeType), "changeType_py": changeType,
                           "commonUserID": request.session["commonUserID"], "user": admin,"isAdmin":True,
                           "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")})
        else:
            return render(request, "Admin/adminChangeInfor.html",
                          {"changeType_js": json.dumps(changeType), "changeType_py": changeType, "user": admin,
                           "isAdmin":True,"allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})

    admin = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
    if changeType == "Email":
        newEmailAdd = request.POST.get("newEmailAdd", "")
        admin.commonEmail = newEmailAdd
        if not newEmailAdd.endswith("@mail.uic.edu.cn"):
            admin.VerifiedUser.delete()
    if changeType == "Name":
        newName = request.POST.get("newName", "")
        admin.commonName = newName
    if changeType == "Password":
        newPassword = request.POST.get("Password", "")
        admin.commonPassword = newPassword
    if changeType == "Image":
        photo = request.FILES.get("photo", "")
        photoName = str(request.session['commonUserID']) + "." + photo.name.split(".")[1]
        photo_resize = Image.open(photo)
        photo_resize.thumbnail((371, 475), Image.ANTIALIAS)
        if os.path.isfile(os.path.join(".", ".", os.getcwd(), "media", str(admin.commonUserImage))):
            os.remove(os.path.join(".", ".", os.getcwd(), "media", str(admin.commonUserImage)))
        photo_resize.save(os.path.join(".", ".", os.getcwd(), "media", "userImage", photoName))
        admin.commonUserImage = "userImage/" + photoName
    admin.save()
    return HttpResponseRedirect(reverse("USFP:adminSuChange", args=(changeType,)))


def adminSuChange(request, changeType):
    try:
        admin = CommonUser.object.get(commonUserID=request.session["commonUserID"])
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    return render(request, "Admin/adminSuChange.html", {"user": admin, "changeType": changeType,"isAdmin":True,
                                                        "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                            "-tagShowNum")[1:11]})


def adminViewArea(request, num, areaID):
    try:
        admin = CommonUser.object.get(commonUserID=request.session["commonUserID"])
        assert admin.VerifiedUser.isAdmin
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    area = Area.object.get(areaID=areaID)
    if area not in admin.VerifiedUser.adminArea.all():
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    users = [i for i in area.CommonUser.filter(isDelete=False) if not i.isVerified()]
    if int(num) < 1:
        num = 1
    else:
        num = int(num)
    pager = Paginator(users, 10)
    try:
        prepageData = pager.page(num)
    except EmptyPage:
        prepageData = pager.page(pager.num_pages)
    begin = (num - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > pager.num_pages:
        end = pager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    pagelist = range(begin, end + 1)
    return render(request, "Admin/adminViewArea.html",
                  {"pager": pager, 'prepageData': prepageData, "pageList": pagelist, "areaID": area.areaID,
                   "areaName": area.areaName,
                   "user": admin,"isAdmin":True,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})


def adminDeleteUsers(request):
    try:
        admin = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
        assert admin.VerifiedUser.isAdmin
        deleteList = [i for i in request.POST.get("listToDelete").split("-") if len(i) != 0]
        try:
            for i in deleteList:
                userToDelete = CommonUser.object.get(commonUserID=int(i))
                if not userToDelete.isManagedBy(admin):
                    return HttpResponse("Fail")
                userToDelete.isDelete = True
                userToDelete.deleteDate = datetime.now()
                userToDelete.save()
                CommonUserOperation.objects.create(commonUser=userToDelete, operationType='deleteUser',
                                                   content="Delete the user", verifiedUser=admin.VerifiedUser)
        except Exception as e:
            print(e)
            return HttpResponse("Fail")
        return HttpResponse("Success")
    except Exception as e:
        print(e)
        return HttpResponse("Fail")


def adminViewOperations(request, areaOperationNum, userOperationNum, suggestionOperationNum):
    try:
        user = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
        assert user.VerifiedUser.isAdmin
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    areaOperations = user.VerifiedUser.AreaOperation.order_by("-operationTakeDate")
    if int(areaOperationNum) < 1:
        areaOperationNum = 1
    else:
        areaOperationNum = int(areaOperationNum)
    areaPager = Paginator(areaOperations, 10)
    try:
        areaPrepageData = areaPager.page(areaOperationNum)
    except EmptyPage:
        areaPrepageData = areaPager.page(areaPager.num_pages)
    begin = (areaOperationNum - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > areaPager.num_pages:
        end = areaPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    areaPageList = range(begin, end + 1)
    userOperations = user.VerifiedUser.UserOperation.order_by("-operationTakeDate")
    if int(userOperationNum) < 1:
        userOperationNum = 1
    else:
        userOperationNum = int(userOperationNum)
    userPager = Paginator(userOperations, 10)
    try:
        userPrepageData = userPager.page(userOperationNum)
    except EmptyPage:
        userPrepageData = userPager.page(userPager.num_pages)
    begin = (userOperationNum - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > userPager.num_pages:
        end = userPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    userPageList = range(begin, end + 1)
    suggestionOperations = user.VerifiedUser.SuggestionOperation.order_by("-operationTakeDate")
    if int(suggestionOperationNum) < 1:
        suggestionOperationNum = 1
    else:
        suggestionOperationNum = int(suggestionOperationNum)
    suggestionPager = Paginator(suggestionOperations, 10)
    try:
        suggestionPrepageData = suggestionPager.page(suggestionOperationNum)
    except EmptyPage:
        suggestionPrepageData = suggestionPager.page(suggestionPager.num_pages)
    begin = (suggestionOperationNum - int(math.ceil(10.0 / 2)))
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
    return render(request, "Admin/adminViewOperations.html",
                  {"areaOpNum": areaOperationNum, 'areaPrepageData': areaPrepageData, "areaPageList": areaPageList,
                   "userOpNum": userOperationNum, "userPrepageData": userPrepageData, "userPageList": userPageList,
                   "suggestionOpNum": suggestionOperationNum, "suggestionPrepageData": suggestionPrepageData,
                   "suggestionPageList": suggestionPageList,
                   "user": user,"isAdmin":True,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]}
                  )


def adminViewUser(request, commonUserID):
    try:
        admin = CommonUser.object.get(commonUserID=request.session["commonUserID"])
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    user = CommonUser.object.get(commonUserID=commonUserID)
    if user.isManagedBy(admin):
        areaNameList = admin.VerifiedUser.adminArea.filter(isDelete=False).values_list('areaName', flat=True)
        return render(request, "Admin/adminViewUser.html",
                      {"userToView": user, "areaNameList": areaNameList, "isVerified": user.isVerified(),"user":admin,
                       "isAdmin":True,
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
    return HttpResponseRedirect(reverse("welcome", args=(1,)))


def adminUpdateUser(request, commonUserID):
    try:
        admin = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
    except KeyError:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    if request.method == "GET":
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    commonUser = CommonUser.object.get(commonUserID=commonUserID)
    if not commonUser.isManagedBy(admin):
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    try:
        if request.POST.get("deletePhoto", "0") == "1":
            if len(str(commonUser.commonUserImage)) != 0:
                if os.path.exists(
                        os.path.join(".", ".", os.getcwd(), "media", "userImage", str(commonUser.commonUserImage))):
                    os.remove(
                        os.path.join(".", ".", os.getcwd(), "media", "userImage", str(commonUser.commonUserImage)))
            commonUser.commonUserImage = None
            CommonUserOperation.objects.create(verifiedUser=admin.VerifiedUser, operationType='updateUser',
                                               commonUser=commonUser, content="Delete photo")
        if request.POST.get("changeArea", "0") == "1":
            originalName = commonUser.area.areaName
            commonUser.area = Area.objects.get(areaName=request.POST.get("newArName"))
            CommonUserOperation.objects.create(verifiedUser=admin.VerifiedUser, operationType='updateUser',
                                               commonUser=commonUser,
                                               content="Original area:" + originalName + " New area:" + request.POST.get(
                                                   "newArName"))
        commonUser.save()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(reverse("USFP:adminViewUser", args=(commonUserID,)))


def adminViewUserSuggestions(request, commonUserID, num):
    admin = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
    user = CommonUser.objects.get(commonUserID=commonUserID)
    if not user.isManagedBy(admin):
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    suggestions = [i for i in user.Suggestion.filter(isDelete=False)]
    if int(num) < 1:
        num = 1
    else:
        num = int(num)
    pager = Paginator(suggestions, 10)
    try:
        prepageData = pager.page(num)
    except EmptyPage:
        prepageData = pager.page(pager.num_pages)
    begin = (num - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > pager.num_pages:
        end = pager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    pagelist = range(begin, end + 1)
    return render(request, "Admin/adminViewUserSuggestions.html",
                  {"pager": pager, 'prepageData': prepageData, "pageList": pagelist, "commonUserID": commonUserID,
                   "user": admin,"isAdmin":True,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})


def adminOperateSuggestions(request):
    try:
        operateType = request.POST.get("operateType")
        admin = CommonUser.object.get(commonUserID=request.session['commonUserID'])
        assert admin.VerifiedUser.isAdmin
        if operateType == "delete":
            listToDelete = [i for i in request.POST.get("listToDelete").split("-") if len(i) != 0]
            for i in listToDelete:
                suggestion = Suggestion.objects.get(suggestionID=int(i))
                suggestion.isDelete = True
                suggestion.deleteDate = datetime.now()
                try:
                    for j in suggestion.tags.all():
                        j.tagShowNum = j.tagShowNum - 1
                        j.save()
                except Exception as e:
                    print(e)
                SuggestionOperation.objects.create(verifiedUser=admin.VerifiedUser, suggestion=suggestion,
                                                   content="Delete the suggestion", operationType='deleteSuggestion')
                suggestion.save()
        elif operateType == "hide":
            listToHide = [i for i in request.POST.get("listToHide").split("-") if len(i) != 0]
            for i in listToHide:
                suggestion = Suggestion.objects.get(suggestionID=int(i))
                suggestion.visible = False
                SuggestionOperation.objects.create(verifiedUser=admin.VerifiedUser, suggestion=suggestion,
                                                   content="Hide the suggestion", operationType='hideSuggestion')
                suggestion.save()
        elif operateType == "show":
            listToShow = [i for i in request.POST.get("listToShow").split("-") if len(i) != 0]
            for i in listToShow:
                suggestion = Suggestion.objects.get(suggestionID=int(i))
                suggestion.visible = True
                SuggestionOperation.objects.create(verifiedUser=admin.VerifiedUser, suggestion=suggestion,
                                                   content="Show the suggestion", operationType='showSuggestion')
                suggestion.save()
        else:
            return HttpResponse("Fail")
        return HttpResponse("Succeed")
    except Exception as e:
        print(e)
        return HttpResponse("Fail")


def adminViewDeletions(request, areaDeletionNum, userDeletionNum, suggestionDeletionNum):
    try:
        user = CommonUser.objects.get(commonUserID=request.session['commonUserID'])
        assert user.VerifiedUser.isAdmin
    except:
        return HttpResponseRedirect(reverse("welcome", args=(1,)))
    areaOperations = user.VerifiedUser.AreaOperation.filter(operationType="deleteArea",
                                                            operationTakeDate__gt=datetime.now() - timedelta(
                                                                weeks=2)).order_by("-operationTakeDate")
    if int(areaDeletionNum) < 1:
        areaDeletionNum = 1
    else:
        areaDeletionNum = int(areaDeletionNum)
    areaPager = Paginator(areaOperations, 10)
    try:
        areaPrepageData = areaPager.page(areaDeletionNum)
    except EmptyPage:
        areaPrepageData = areaPager.page(areaPager.num_pages)
    begin = (areaDeletionNum - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > areaPager.num_pages:
        end = areaPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    areaPageList = range(begin, end + 1)
    userOperations = user.VerifiedUser.UserOperation.filter(operationType="deleteUser",
                                                            operationTakeDate__gt=datetime.now() - timedelta(
                                                                weeks=2)).order_by("-operationTakeDate")
    if int(userDeletionNum) < 1:
        userDeletionNum = 1
    else:
        userDeletionNum = int(userDeletionNum)
    userPager = Paginator(userOperations, 10)
    try:
        userPrepageData = userPager.page(userDeletionNum)
    except EmptyPage:
        userPrepageData = userPager.page(userPager.num_pages)
    begin = (userDeletionNum - int(math.ceil(10.0 / 2)))
    if begin < 1:
        begin = 1
    end = begin + 9
    if end > userPager.num_pages:
        end = userPager.num_pages
    if end <= 10:
        begin = 1
    else:
        begin = end - 9
    userPageList = range(begin, end + 1)
    suggestionOperations = user.VerifiedUser.SuggestionOperation.filter(operationType="deleteSuggestion",
                                                                        operationTakeDate__gt=datetime.now() - timedelta(
                                                                            weeks=2)).order_by("-operationTakeDate")
    if int(suggestionDeletionNum) < 1:
        suggestionDeletionNum = 1
    else:
        suggestionDeletionNum = int(suggestionDeletionNum)
    suggestionPager = Paginator(suggestionOperations, 10)
    try:
        suggestionPrepageData = suggestionPager.page(suggestionDeletionNum)
    except EmptyPage:
        suggestionPrepageData = suggestionPager.page(suggestionPager.num_pages)
    begin = (suggestionDeletionNum - int(math.ceil(10.0 / 2)))
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
    return render(request, "Admin/adminViewDeletions.html",
                  {"areaDeletionNum": areaDeletionNum, 'areaPrepageData': areaPrepageData, "areaPageList": areaPageList,
                   "userDeletionNum": userDeletionNum, "userPrepageData": userPrepageData, "userPageList": userPageList,
                   "suggestionDeletionNum": suggestionDeletionNum, "suggestionPrepageData": suggestionPrepageData,
                   "suggestionPageList": suggestionPageList,"isAdmin":True,
                   "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11],
                   "user": user}
                  )


def adminAnnulDeletions(request):
    try:
        user = CommonUser.object.get(commonUserID=request.session['commonUserID'])
        assert user.VerifiedUser.isAdmin
        areaOperationList = [i for i in request.POST.get('areaOperationList').split('-') if len(i) != 0]
        userOperationList = [i for i in request.POST.get('userOperationList').split('-') if len(i) != 0]
        suggestionOperationList = [i for i in request.POST.get('suggestionOperationList').split('-') if len(i) != 0]
        for i in areaOperationList:
            areaOperation = AreaOperation.objects.get(areaOperationID=int(i))
            area = areaOperation.area
            area.isDelete = False
            area.deleteDate = None
            area.save()
            areaOperation.delete()
        for i in userOperationList:
            userOperation = CommonUserOperation.objects.get(commonUserOperationID=int(i))
            user = userOperation.commonUser
            user.isDelete = False
            user.deleteDate = None
            user.save()
            userOperation.delete()
        for i in suggestionOperationList:
            suggestionOperation = SuggestionOperation.objects.get(suggestionOperationID=int(i))
            suggestion = suggestionOperation.suggestion
            suggestion.isDelete = False
            suggestion.deleteDate = None
            try:
                for j in suggestion.tags.all():
                    j.tagShowNum = j.tagShowNum + 1
                    j.save()
            except Exception as e:
                print(e)
            suggestion.save()
            suggestionOperation.delete()
        return HttpResponse('Success')
    except Exception as e:
        print(e)
        return HttpResponse('Success')


def adminViewUnhandledSuggestion(request, num):
    try:
        unhandledSuggestionList = []
        admin = CommonUser.object.get(commonUserID=request.session['commonUserID'])
        for area in admin.VerifiedUser.adminArea.all():
            for user in area.CommonUser.all():
                unhandledSuggestionList.extend(list(user.Suggestion.filter(visible=False, isDelete=False)))
        if int(num) < 1:
            num = 1
        else:
            num = int(num)
        suggestionPager = Paginator(unhandledSuggestionList, 10)
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
        return render(request, "Admin/adminViewUnhandledSuggestion.html",
                      {"suggestionNum": num, 'suggestionPrepageData': suggestionPrepageData,
                       "suggestionPageList": suggestionPageList,
                       "user": admin,"isAdmin":True,
                       "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by("-tagShowNum")[1:11]})
    except Exception as e:
        print(e)
        return redirect("welcome")


def adminViewOneSuggestion(request, suggestionID, num):
    try:
        user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
        suggestion = Suggestion.object.get(suggestionID=suggestionID)
        assert user.isVerified()
        assert user.VerifiedUser.isAdmin
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
        isManagedBy = suggestion.commonUser.area in user.VerifiedUser.adminArea.all()
        return render(request, "Admin/adminViewOneSuggestion.html", {"suggestion": suggestion,
                                                                     "isManagedBy": isManagedBy,
                                                                     "isReplied": suggestion.isReplied(),
                                                                     'user': user,"isAdmin":True,
                                                                     'isAuthor': (
                                                                                 suggestion.commonUser.commonUserID == user.commonUserID),
                                                                     'replySuggestionPrepageData': replySuggestionPrepageData,
                                                                     'replySuggestionPageList': replySuggestionPageList,
                                                                     "suggestion_tags": suggestion.tags.all(),
                                                                     "allTags": Tag.objects.filter(
                                                                         tagShowNum__gt=0).order_by("-tagShowNum")[
                                                                                1:11]})
    except Exception as e:
        print(e)
        return redirect("USFP:adminInfor")


def adminSubmitComment(request, suggestionID):
    try:
        replyContent = request.POST.get("comment", "")
        choice = int(request.POST.get("choice", 0))
        user = CommonUser.object.get(commonUserID=request.session['commonUserID'])
        suggestion = Suggestion.objects.get(suggestionID=suggestionID)
        assert suggestion.commonUser.area in user.VerifiedUser.adminArea.all()
        if len(replyContent) != 0:
            replySuggestion = Suggestion.objects.create(visible=True, content=replyContent, commonUser=user)
            ReplySuggestion.objects.create(selfSuggestion=replySuggestion, suggestionToReply=suggestion)
        if choice == 1:
            suggestion.isDelete = True
            suggestion.deleteDate = datetime.now()
            try:
                for j in suggestion.tags.all():
                    j.tagShowNum = j.tagShowNum - 1
                    j.save()
            except Exception as e:
                print(e)
            suggestion.save()
            SuggestionOperation.objects.create(verifiedUser=user.VerifiedUser, suggestion=suggestion,
                                               content="Delete the suggestion", operationType='deleteSuggestion')
        if choice == 2:
            suggestion.visible = True
            suggestion.save()
            SuggestionOperation.objects.create(verifiedUser=user.VerifiedUser, suggestion=suggestion,
                                               content="Show the suggestion", operationType='showSuggestion')
        if choice == 3:
            suggestion.visible = False
            suggestion.save()
            SuggestionOperation.objects.create(verifiedUser=user.VerifiedUser, suggestion=suggestion,
                                               content="Hide the suggestion", operationType='hideSuggestion')
        return HttpResponseRedirect(reverse("USFP:adminSuSubmitComment", args=(suggestionID,)))
    except Exception as e:
        print(e)
        return redirect("USFP:adminInfor")


def adminSuSubmitComment(request, suggestionID):
    user = CommonUser.object.get(commonUserID=request.session.get('commonUserID', 5))
    suggestion = Suggestion.objects.get(suggestionID=suggestionID)
    return render(request, "Admin/adminSuSubmitComment.html", {"suggestion": suggestion, 'user': user,"isAdmin":True,
                                                               "allTags": Tag.objects.filter(tagShowNum__gt=0).order_by(
                                                                   "-tagShowNum")[1:11]})
