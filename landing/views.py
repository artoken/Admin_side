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
with open('./contracts/Diamond.json') as f:
    abi = json.loads(f.read())

art_token = web3.eth.contract(address=config["address_token"], abi=abi["abi"])

with open('./contracts/AuctionBox.json') as f:
    abi = json.loads(f.read())

with open('./contracts/ClosedAuctionBox.json') as f:
    abiClosedBox = json.loads(f.read())

auction_box = web3.eth.contract(config["address_box"], abi=abi["abi"])
closed_auction_box = web3.eth.contract(config["address_closed_box"], abi=abiClosedBox["abi"])
erc20 = config["erc_20"]
insertationSorter = config["sorter"]

account_owner = config["owner"]


def get_time(timestamp):
    return datetime.datetime.fromtimestamp( int(f"{timestamp}") ).strftime('%Y-%m-%d %H:%M:%S')
    #return datetime.datetime.fromtimestamp( int(f"{timestamp}") ).strftime('%d-%m-%Y')

# Вывод всей информации о токенах на главной странице
def landing(request):
    
    tokens_in_system = art_token.functions.totalSupply().call()
    
    tokenIds = art_token.functions.getTokenIds().call()
    tokensInSystem = len(tokenIds)

    infoAboutTokens = []
    for index in tokenIds:
        infoAboutTokens.append([index]+art_token.functions.getArtToken(index).call())

    links_for_tokens = [art_token.functions.tokenURI(index).call() for index in tokenIds]
    print(links_for_tokens)
    for i in range(len(infoAboutTokens)):
        part = infoAboutTokens[i]
        part.append('https://ipfs.io/ipfs/'+ links_for_tokens[i])

    code_names = ['ID', 'Entity', 'Name', 'Author', 'Year', 'Extra', 'Link']

    info_to_render = []
    for info in infoAboutTokens:
        info_to_render.append(dict(zip(code_names, info)))

    style = 'color:#fff; background-color:#B22222'
    return render(request, 'artproject_owner/index.html', locals())

# Токенизация актива
def token(request):
    idform = CreateToken()
    text_for_user = ""
    style = 'color:#fff; background-color:#B22222'
    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        tokenId = int(request.POST.get("idform").rstrip())
        owner = request.POST.get("owner").rstrip()
        entity = request.POST.get("entity").rstrip()
        name = request.POST.get("name").rstrip()
        author = request.POST.get("author").rstrip()
        year = int(request.POST.get("year").rstrip())
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

        tx = art_token.functions.mint(f'{owner}', tokenId, f'{entity}', f'{name}', f'{author}', year, f'{extra_data}').buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        tx = art_token.functions.setTokenURI(tokenId, f'{image_link}').buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        
        text_for_user = "Токен успешно создан"    
    return render(request, 'artproject_owner/tokenization.html', locals())

# Вывод всех открытых аукционов
def auction(request):
    closeform = CloseAuction()
    auctions_in_system = auction_box.functions.returnAllAuctions().call()
    style = 'color:#fff; background-color:#B22222'
    with open('./contracts/EnglishAuction.json') as f:
        abi = json.loads(f.read())
    
    info_to_render = []
    code_names = ['IDINTERN','BNFCRY', 'ENDTIME', 'HIGHBIDDER', 'HIGHBID','STARTPRICE', 'AUCTADDR', 'STEPMIN', 'STEPMAX', 'LINK', 'STATE']
    for auction_address in auctions_in_system:
        auction_contract = web3.eth.contract(address=auction_address, abi=abi["abi"])
        
        closed = auction_contract.functions.is_ended().call()
        if not closed:
            id_internal = auction_contract.functions.token_id().call()
            state = auction_contract.functions.auctionState().call()
            print("Стадия аукциона", state)
            if state == 0:
                stateString = "Аукцион на стадии инициализации"
            elif state == 1:
                stateString = "Аукцион на стадии принятия ставок"
            else:
                stateString = "Аукцион на стадии раскрытия победителя"
                
            beneficiary = auction_contract.functions.beneficiary().call()
            auctionEndTime = auction_contract.functions.auctionEndTime().call()
            auctionEndTime_convert = get_time(int(auctionEndTime))

            link = 'https://ipfs.io/ipfs/'+art_token.functions.tokenURI(id_internal).call()
            
            highestBidder = auction_contract.functions.highestBidder().call()
            highestBid = auction_contract.functions.highestBid().call()/10**18
            startPrice = auction_contract.functions.startPrice().call()/10**18
            stepmin = auction_contract.functions.step_min().call()/10**18
            stepmax = auction_contract.functions.step_max().call()/10**18 
            info = [id_internal, beneficiary, auctionEndTime_convert, highestBidder, highestBid, startPrice, auction_address, stepmin, stepmax, link, stateString]
            info_to_render.append(dict(zip(code_names, info)))
    
    # закрываем открытый аукцион
    if "send" in request.POST:
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        address_auction = request.POST.get("auction_address").rstrip()
        auction_contract = web3.eth.contract(address=address_auction, abi=abi["abi"])

        tx = auction_contract.functions.auctionEnd().buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    # меняем этап открытого аукциона
    if "sendChange" in request.POST:
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        address_auction = request.POST.get("auction_address").rstrip()
        auction_contract = web3.eth.contract(address=address_auction, abi=abi["abi"])

        currentState = auction_contract.functions.auctionState().call()
        if currentState <= 1:
            tx = auction_contract.functions.changeAuctionState(currentState+1).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
            signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
            web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    return render(request, 'artproject_owner/auction.html', locals())

# Вывод всех закрытых аукционов
def closed_auction(request):
    closeform = CloseAuction()
    auctions_in_system = closed_auction_box.functions.returnAllAuctions().call()
    style = 'color:#fff; background-color:#B22222'
    with open('./contracts/HashedClosedAuction.json') as f:
        abi = json.loads(f.read())
    
    info_to_render = []
    code_names = ['IDINTERN','BNFCRY', 'ENDTIME', 'STARTPRICE', 'AUCTADDR', 'MAXBIDCOUNT','LINK', 'STATE']
    for auction_address in auctions_in_system:
        auction_contract = web3.eth.contract(address=auction_address, abi=abi["abi"])
        
        closed = auction_contract.functions.is_ended().call()
        if not closed:
            id_internal = auction_contract.functions.token_id().call()
            state = auction_contract.functions.auctionState().call()
            print("Стадия аукциона", state)
            if state == 0:
                stateString = "Аукцион на стадии инициализации"
            elif state == 1:
                stateString = "Аукцион на стадии принятия ставок"
            elif state == 2:
                stateString = "Аукцион на стадии доказательства ставок"
            else:
                stateString = "Аукцион на стадии раскрытия победителя"
                
            beneficiary = auction_contract.functions.beneficiary().call()
            auctionEndTime = auction_contract.functions.auctionEndTime().call()
            auctionEndTime_convert = get_time(int(auctionEndTime))

            link = 'https://ipfs.io/ipfs/'+art_token.functions.tokenURI(id_internal).call()
            

            minBid = auction_contract.functions.startPrice().call()/10**18
            maxBidCount = auction_contract.functions.auctionMaximumBidOverwriteCount().call()
            
            info = [id_internal, beneficiary, auctionEndTime_convert, minBid, auction_address, maxBidCount, link, stateString]
            info_to_render.append(dict(zip(code_names, info)))

    # закрываем аукцион
    if "send" in request.POST:
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        address_auction = request.POST.get("auction_address").rstrip()
        auction_contract = web3.eth.contract(address=address_auction, abi=abi["abi"])

        tx = auction_contract.functions.revealWinner().buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    # меняем этап аукциона
    if "sendChange" in request.POST:
        password = request.POST.get("password").rstrip()
        password = '0x'+password
        address_auction = request.POST.get("auction_address").rstrip()
        auction_contract = web3.eth.contract(address=address_auction, abi=abi["abi"])

        currentState = auction_contract.functions.auctionState().call()
        if currentState <= 2:
            tx = auction_contract.functions.changeAuctionState(currentState+1).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
            signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
            web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    return render(request, 'artproject_owner/close_auction.html', locals())

# Старт открытого аукциона
def start_auction(request):
    auctionform = CreateAuction()
    text_for_user = ""
    style = 'color:#fff; background-color:#B22222'
    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        token_id = int(request.POST.get("id_internal").rstrip())
        benificiary = request.POST.get("benificiary").rstrip()
        auctiontime = int(request.POST.get("auctiontime").rstrip())
        startprice = int(int(request.POST.get("startprice").rstrip())*(10**18))
        step_min = int(request.POST.get("stepmin").rstrip())
        step_max = int(request.POST.get("stepmax").rstrip())
        tokenAddress = config["address_token"]
        tx = auction_box.functions.createAuction(config["address_token"], f'{benificiary}',auctiontime, startprice, token_id, step_min, step_max).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        return  render(request, 'artproject_owner/start_auction.html', locals())

    
    return render(request, 'artproject_owner/start_auction.html', locals())

# Старт закрытого аукциона
def start_closed_auction(request):
    auctionform = CreateClosedAuction()
    text_for_user = ""
    style = 'color:#fff; background-color:#B22222'
    if request.method == "POST":
        password = request.POST.get("password").rstrip()
        token_id = int(request.POST.get("id_internal").rstrip())
        benificiary = request.POST.get("benificiary").rstrip()
        auctiontime = int(request.POST.get("auctiontime").rstrip())
        startprice = int(int(request.POST.get("startprice").rstrip())*(10**18))
        tokenAddress = config["address_token"]
        maxBid = int(request.POST.get("maxBidCount").rstrip())
        tx = closed_auction_box.functions.createAuction(erc20, tokenAddress, auctiontime, f'{benificiary}', startprice, token_id, maxBid).buildTransaction({'nonce': web3.eth.getTransactionCount(account_owner), 'from': account_owner})
        signed_tx = web3.eth.account.signTransaction(tx, private_key=password)
        web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        return  render(request, 'artproject_owner/start_auction.html', locals())

    
    return render(request, 'artproject_owner/start_auction.html', locals())