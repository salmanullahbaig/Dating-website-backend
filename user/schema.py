from django.db.models import fields
from django.db.models.query_utils import subclasses
from framework.api.API_Exception import APIException
import graphene
from user.models import *
#from framework.api.API_Exception import APIException
from gallery.models import Photo
from gallery.schema import PhotoObj
from user import models
from graphene.utils.resolve_only_args import resolve_only_args
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from .utils import get_gender_from_code
from datetime import datetime, timedelta

from django.db import connection as conn

class CoinSettingType(DjangoObjectType):
    class Meta:
        model = models.CoinSettings
        fields = '__all__'

class CoinHistoryType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('gift_coins', 'purchase_coins',)

class UserPhotoType(DjangoObjectType):
    url = graphene.String()
    user = graphene.String()

    class Meta:
        model = models.UserPhoto
        fields = ('id', 'url', 'user')
    
    def resolve_url(self, info):
        if self.file:
            try:
                url=info.context.build_absolute_uri(self.file.url)
            except:
                url=self.file.url
            return url
        else:
            return self.file_url

    def resolve_user(self, info):
        return self.user.id

class Gender(graphene.ObjectType):
    code = graphene.String()
    name = graphene.String()

    def resolve_code(self, info):
        return self
    
    def resolve_name(self, info):
        return get_gender_from_code(self)

class isOnlineObj(graphene.ObjectType):
    id = graphene.String()
    isOnline = graphene.Boolean()
    username = graphene.String()

    def resolve_isOnline(self, info):
        return self['isOnline']

    def resolve_username(self, info):
        return self['username']

    def resolve_id(self, info):
        return self['id']

class OnlineObj(graphene.ObjectType):
    isOnline = graphene.Boolean()

    def resolve_isOnline(self, info):
        if isinstance(self, User):
            return self.isOnline

#list
class isLastLoginObj(graphene.ObjectType):
    id = graphene.String()
    username = graphene.String()
    last_login = graphene.String()

    class Meta:
        model = User
        fields = ("id", "username", 'last_login',)

#single
class lastLoginObj(graphene.ObjectType):
    id = graphene.String()
    username = graphene.String()
    last_login = graphene.String()

    class Meta:
        model = User
        fields = ("id", "username", 'last_login',)



class UploadFileObj(graphene.ObjectType):
    id = graphene.String()
    success = graphene.Boolean()
    image_data = graphene.String()

class coinsResponseObj(graphene.ObjectType):
    id = graphene.String()
    coins = graphene.Int()
    success = graphene.Boolean()

class blockResponseObj(graphene.ObjectType):
    id = graphene.String()
    username = graphene.String()
    success = graphene.Boolean()

class updateCoin(graphene.Mutation):

    class Arguments:
        coins = graphene.Int()
        id = graphene.String()

    Output = coinsResponseObj

    def mutate(self, info, coins=None, id=None):
        user = User.objects.get(id=id)
        coin = user.coins
        print(coin)

        if coins is not None:
            user = user.addCoins(coins)

        user.save()
        return coinsResponseObj(id=user.id, success=True, coins=user.coins)

class ChatCoin(graphene.Mutation):
    class Arguments:
        id = graphene.String()
        method = graphene.String()

    Output = coinsResponseObj

    def mutate(self, info, method=None, id=None):
        user = User.objects.get(id=id)
        if user.is_anonymous:
            return APIException("You must be logged in to use coins")
        coin = user.coins
        print(coin)
        # if method.upper() == "MESSAGE":
        #     user = user.deductCoin(19)

            
            

        # elif method.upper() == "IMAGE_MESSAGE":
        #     user = user.deductCoin(60)
            
            
        coin_settings = CoinSettings.objects.all()
        for coin_setting in coin_settings:
            if method.upper() == coin_setting.method.upper():
                if coin < coin_setting.coins_needed:
                    return APIException("Insufficient Coins")
                user.deductCoins(coin_setting.coins_needed)
                break
        else:
            return APIException("Please enter a valid method")
        if method.upper() == "PROFILE_PICTURE":
            user.photos_quota += 1
        user.save()
        return coinsResponseObj(id=user.id, success=True, coins=user.coins)

# class UpdateProfilePic(graphene.Mutation):
#     Output = UploadFileObj

#     class Arguments:
#         id = graphene.String()
#         image_data = graphene.String()

#     def mutate(self, info,  id=None, image_data=None):
#         user = User.objects.get(id=id)
#         avatar = image_data
#         user.avatar = avatar
#         user.save()
#         return UploadFileObj(id=user.id, image_data=user.avatar, success=True)

class MutationResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()

class DeleteAvatarPhoto(graphene.Mutation):
    Output = MutationResponse

    class Arguments:
        id = graphene.String()
    
    def mutate(self, info, id=None):
        user = info.context.user
        print(user)
        if not user.is_authenticated:
            return MutationResponse(success=False, message="Authentication required")
        
        photos = models.UserPhoto.objects.filter(id=id)
        
        if(photos.count() == 0):
            return MutationResponse(success=False, message="Image not found")
        
        photo = photos[0]

        if photo.user.id != user.id:
            return MutationResponse(success=False, message="You are not authorized to delete this image")

        photo.delete()
        return MutationResponse(success=True, )

class blockUser(graphene.Mutation):
    Output = blockResponseObj

    class Arguments:
        id = graphene.String()
        blocked_id = graphene.String()

    def mutate(self, info, id, blocked_id):
        blckd_user = User.objects.get(id=blocked_id)
        user = User.objects.get(id=id)
        user.blockedUsers.add(blckd_user)
        user.save()

        return blockResponseObj(id=blckd_user.id, username=blckd_user.username, success=True)

class unblockUser(graphene.Mutation):
    Output = blockResponseObj

    class Arguments:
        id = graphene.String()
        blocked_id = graphene.String()

    def mutate(self, info, id, blocked_id):
        blckd_user = User.objects.get(id=blocked_id)
        user = User.objects.get(id=id)
        print("======================")
        print(user.blockedUsers)
        print("======================")
        user.blockedUsers.clear()
        user.save()

        return blockResponseObj(id=blckd_user.id, username=blckd_user.username, success=True)


class blockedUsers(graphene.ObjectType):
    id = graphene.String()
    username = graphene.String()
    def resolve_id(self, info):
        return self['id']
    
    def resolve_username(self, info):
        return self['username']

class Query(graphene.ObjectType):

    usersOnline = graphene.List(isOnlineObj)
    isOnline = graphene.Field(OnlineObj, id=graphene.String(required=True))

    inactiveUsers =  graphene.List(isLastLoginObj, from_time=graphene.String(required=True), to_time=graphene.String(required=True))
    lastLogin =  graphene.Field(lastLoginObj, id=graphene.String(required=True))

    blockedUsers = graphene.List(blockedUsers)

    coinSettings = graphene.List(CoinSettingType)
    
    # depricated
    # photos = graphene.List(PhotoObj, id=graphene.String(required=True))
    
    def resolve_usersOnline(self, info):
        try:
            return User.objects.filter(isOnline=True).values('isOnline','username','id')
        except:
            raise Exception("try again")

    def resolve_isOnline(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            user = User.objects.get(id=id)
            return user
        else:
            raise Exception('Id is a required parameter')

    def resolve_lastLogin(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                raise Exception('User not found')

            return user
        else:
            raise Exception('Id is a required parameter')

    def resolve_inactiveUsers(self, info, from_time='0.5', to_time='1'):
        """
        from_time and to_time is float
        30 minutes to 1 hour => 0.5 - 1
        1 hour to 5 hours => 1 - 5 
        ...
        """
        try:
            from2 = float(from_time)
        except ValueError:
            raise Exception("from_time needs to be a number of hours. can be float.")
        
        try:
            to2 = float(to_time)
        except ValueError:
            raise Exception("to_time needs to be a number of hours. can be float.")
            
        if float(from_time) > float(to_time):
            raise Exception("from_time cant be greater than to_time")

        if float(from_time) < 1:
            from_time = float(from_time) * 60
            from_time = datetime.today() - timedelta(hours=0, minutes=int(from_time))
        elif float(from_time) >= 1 and float(from_time) <= 24:
            minutes = 0
            if float(from_time) != int(from_time):
                minutes = int((float(from_time) - int(from_time))*60)
            from_time = datetime.today() - timedelta(hours=int(from_time), minutes=int(minutes))
        else:
            from_time = int(from_time) / 24
            hours = 0
            if float(from_time) != int(from_time):
                hours = int((float(from_time) - int(from_time))*24)
            from_time = datetime.today() - timedelta(days=int(from_time), hours=int(hours))

        if float(to_time) < 1:
            to_time = float(to_time) * 60
            to_time = datetime.today() - timedelta(hours=0, minutes=int(to_time))
        elif float(to_time) >= 1 and float(to_time) <= 24:
            minutes = 0
            if float(to_time) != int(to_time):
                minutes = int((float(to_time) - int(to_time))*60)
            to_time = datetime.today() - timedelta(hours=int(to_time), minutes=int(minutes))
        else:
            to_time = float(to_time) / 24
            hours = 0
            if float(to_time) != int(to_time):
                hours = int((float(to_time) - int(to_time))*24)
            to_time = datetime.today() - timedelta(days=int(to_time), hours=int(hours))
        try:
            from_time = from_time.strftime("%Y-%m-%d %H:%M:%S")
            to_time = to_time.strftime("%Y-%m-%d %H:%M:%S")
            users = User.objects.filter(last_login__range=(to_time,from_time)).values('id', 'username','last_login')
            return users
        except Exception as e:
            raise Exception("try again", e)


    def resolve_blockedUsers(self, info):
        id = info.context.user.id
        user = User.objects.get(id=id)
        return user.blockedUsers.all().values('id', 'username')
    
    def resolve_coinSettings(self, info):
        return CoinSettings.objects.all()

    # depricated
    # def resolve_photos(self, info, **kwargs):
    #     id = kwargs.get('id')
    #     if id is None:
    #         return Exception("Id is a required parameter")
    #     user = get_user_model().objects.get(id=id)
    #     return Photo.objects.filter(user=user)

class Mutation(graphene.ObjectType):
    updateCoin = updateCoin.Field()
    # depricated
    # UpdateProfilePic = UpdateProfilePic.Field()
    deleteAvatarPhoto = DeleteAvatarPhoto.Field()
    blockUser = blockUser.Field()
    unblockUser = unblockUser.Field()
    deductCoin = ChatCoin.Field()
