from django import forms
from django.forms import TextInput

from django.forms import CharField, Form, PasswordInput

class CreateToken(forms.Form):
    password = CharField(widget=PasswordInput())
    idform_ext = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Внешний ID',
                                    'class': "mt-4 form-control"}))
    idform = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Внутренний ID',
                                    'class': "mt-4 form-control"}))
    share = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Доля в токене',
                                    'class': "mt-4 form-control"}))
    owner = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Владелец',
                                    'class': "mt-4 form-control"}))
    entity = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Сущность',
                                    'class': "mt-4 form-control"}))
    name = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Название',
                                    'class': "mt-4 form-control"}))
    author = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Автор',
                                    'class': "mt-4 form-control"}))
    license_field = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Лицензия',
                                    'class': "mt-4 form-control"}))
    year = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Год создания',
                                    'class': "mt-4 form-control"}))
    genuineness = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Аутентичность',
                                    'class': "mt-4 form-control"}))
    extra_data = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Дополнительная информация',
                                    'class': "mt-4 form-control"}))

    



class CreateAuction(forms.Form):
    password = CharField(widget=PasswordInput())

    id_internal = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Внутренний ID токена',
                                    'class': "mt-4 form-control"}))

    id_external = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Внешний ID токена',
                                    'class': "mt-4 form-control"}))

    benificiary = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Адрес бенифициара',
                                    'class': "mt-4 form-control"}))
    auctiontime = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Время аукциона',
                                    'class': "mt-4 form-control"}))
    startprice = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Начальная цена (bnb)',
                                    'class': "mt-4 form-control"}))
    stepmin = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Минимальный шаг (%)',
                                    'class': "mt-4 form-control"}))
    stepmax = forms.CharField(label='',
    widget=forms.NumberInput(attrs={'placeholder': 'Максимальный шаг (%)',
                                    'class': "mt-4 form-control"}))


class CloseAuction(forms.Form):
    password = CharField(widget=PasswordInput())

    auction_address = forms.CharField(label='',
    widget=forms.TextInput(attrs={'placeholder': 'Адрес аукциона',
                                    'class': "mt-4 form-control"}))
