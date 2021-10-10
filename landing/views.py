from django.shortcuts import render
import requests
from web3 import Web3
import json
from .forms import *
import datetime 
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import pathlib

ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

with open("config.json", "r") as read_file:
    config = json.load(read_file)

connect = web3.isConnected()
with open('../Client_auctions_and_deploy/client/src/contracts/ART_CONTRACT.json') as f:
    abi = json.loads(f.read())

art_token = web3.eth.contract(address=config["address_token"], abi=abi["abi"])

with open('../Client_auctions_and_deploy/client/src/contracts/AuctionBox.json') as f:
    abi = json.loads(f.read())


auction_box = web3.eth.contract(config["address_box"], abi=abi["abi"])

account_owner = config["owner"]


def get_time(timestamp):
    return datetime.datetime.fromtimestamp( int(f"{timestamp}") ).strftime('%Y-%m-%d %H:%M:%S')
    #return datetime.datetime.fromtimestamp( int(f"{timestamp}") ).strftime('%d-%m-%Y')


def landing(request):
    
    tokens_in_system = art_token.functions.totalSupply().call()
    share_ids_in_system = [art_token.functions.ids_external(i).call() for i in range(tokens_in_system)]
    share_ids_in_system = list(set(share_ids_in_system))

    token_ids = [art_token.functions.share_to_token(i).call() for i in share_ids_in_system]
    token_ids = list(set(token_ids))
    a = [art_token.functions.get_art_by_share_id(i).call() for i in share_ids_in_system]

    token_ids_in_system = [int(part[0]) for part in a]

    keys_list = [str(part) for part in token_ids_in_system]
    values_list = share_ids_in_system
    zip_iterator = zip(keys_list, values_list)
    a_dictionary = dict(zip_iterator)

    token_ids_in_system = list(set(token_ids_in_system))
    tokens_in_system = len(token_ids_in_system)

    info_about_tokens = []
    for i in token_ids_in_system:
        info_about_tokens.append(art_token.functions.get_art_by_share_id(a_dictionary[str(i)]).call())

    links_for_tokens = [art_token.functions.get_link_by_token_id(int(i)).call() for i in token_ids_in_system]

    for i in range(len(info_about_tokens)):
        part = info_about_tokens[i]
        part.append('https://ipfs.io/ipfs/'+ links_for_tokens[i])
    code_names = ['ID', 'Owner','Entity', 'Name', 'Author', 'License', 'Year', 'Orig', 'Extra', 'Link']

    info_to_render = []
    for info in info_about_tokens:
        info_to_render.append(dict(zip(code_names, info)))

    style = 'color:#fff; background-color:#B22222'
    return render(request, 'artproject_owner/index.html', locals())

def token(request):
    idform = CreateToken()
    text_for_user = ""
    style = 'color:#fff; background-color:#B22222'
    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        id_internal = int(request.POST.get("idform").rstrip())
        id_external = int(request.POST.get("idform_ext").rstrip())
        share = int(request.POST.get("share").rstrip())
        owner = request.POST.get("owner").rstrip()
        entity = request.POST.get("entity").rstrip()
        name = request.POST.get("name").rstrip()
        author = request.POST.get("author").rstrip()
        license_field = request.POST.get("license_field").rstrip()
        year = int(request.POST.get("year").rstrip())
        genuineness = request.POST.get("genuineness").rstrip()
        extra_data = request.POST.get("extra_data").rstrip()
        
        myfile = request.FILES['myfile']
        fs = FileSystemStorage('static/img')
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        params = (
            ('pin', 'false'),
        )
        files = {'media': open(str(pathlib.Path('./static/img').resolve())+uploaded_file_url, 'rb')}
        response = requests.post('https://ipfs.infura.io:5001/api/v0/add', params=params, files=files)
        resp = json.loads(response.text)
        image_link = resp['Hash']

        tx = art_token.functions.mint(id_external ,id_internal,f'{owner}', share).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        tx = art_token.functions.set_art_token(id_internal, f'{entity}', f'{name}', f'{author}', f'{license_field}', year, f'{genuineness}', f'{extra_data}', f'{image_link}').buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        
        text_for_user = "Токен успешно создан"    
    return render(request, 'artproject_owner/tokenization.html', locals())


def auction(request):
    closeform = CloseAuction()
    auctions_in_system = auction_box.functions.returnAllAuctions().call()
    style = 'color:#fff; background-color:#B22222'
    with open('../Client_auctions_and_deploy/client/src/contracts/EnglishAuction.json') as f:
        abi = json.loads(f.read())
    
    info_to_render = []
    code_names = ['IDINTERN','BNFCRY', 'ENDTIME', 'HIGHBIDDER', 'HIGHBID','STARTPRICE', 'AUCTADDR', 'STEPMIN', 'STEPMAX', 'LINK']
    for auction_address in auctions_in_system:
        auction_contract = web3.eth.contract(address=auction_address, abi=abi["abi"])
        
        closed = auction_contract.functions.is_ended().call()
        if not closed:
            id_internal = auction_contract.functions.token_id().call()
            print(id_internal)
            beneficiary = auction_contract.functions.beneficiary().call()
            auctionEndTime = auction_contract.functions.auctionEndTime().call()
            auctionEndTime_convert = get_time(int(auctionEndTime))

            link = 'https://ipfs.io/ipfs/'+art_token.functions.get_link_by_token_id(id_internal).call()
            
            highestBidder = auction_contract.functions.highestBidder().call()
            highestBid = auction_contract.functions.highestBid().call()/10**18
            startPrice = auction_contract.functions.startPrice().call()/10**18
            stepmin = auction_contract.functions.step_min().call()/10**18
            stepmax = auction_contract.functions.step_max().call()/10**18 
            info = [id_internal, beneficiary, auctionEndTime_convert, highestBidder, highestBid, startPrice, auction_address, stepmin, stepmax, link]
            info_to_render.append(dict(zip(code_names, info)))

    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        address_auction = request.POST.get("auction_address").rstrip()
        auction_contract = web3.eth.contract(address=address_auction, abi=abi["abi"])

        tx = auction_contract.functions.auctionEnd().buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        highestBidder = auction_contract.functions.highestBidder().call()

        share_id = int(auction_contract.functions.share_id().call())
        
        owner_of_token = art_token.functions.ownerOf(share_id).call()

        tx = art_token.functions.safeTransferFrom(f'{owner_of_token}', f'{highestBidder}', share_id).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    return render(request, 'artproject_owner/auction.html', locals())


def start_auction(request):
    auctionform = CreateAuction()
    text_for_user = ""
    style = 'color:#fff; background-color:#B22222'
    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        id_internal = int(request.POST.get("id_internal").rstrip())
        id_external = int(request.POST.get("id_external").rstrip())
        benificiary = request.POST.get("benificiary").rstrip()
        auctiontime = int(request.POST.get("auctiontime").rstrip())
        startprice = int(request.POST.get("startprice").rstrip())
        step_min = int(request.POST.get("stepmin").rstrip())
        step_max = int(request.POST.get("stepmax").rstrip())
        tx = auction_box.functions.createAuction(address_token, f'{benificiary}',auctiontime, startprice, id_external, id_internal, step_min, step_max).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        return  render(request, 'artproject_owner/start_auction.html', locals())

    
    return render(request, 'artproject_owner/start_auction.html', locals())