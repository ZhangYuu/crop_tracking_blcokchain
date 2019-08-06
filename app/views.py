import datetime
import json
import os
import requests
from flask import render_template, redirect, request, send_from_directory

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

grass_ID=0 #这个数字重启服务器会被重置，需要修改

posts = []

def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        dic = {}
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                print(tx)
                if tx["is_delete_block"] == 1:
                    index = dic[tx["del_hash"]]
                    print("deleted block index",index)
                    content[index]["is_deleted"] = "true"
                    continue

                tx["index"] = block["index"]
                tx["hash"] = block["hash"]
                tx["is_deleted"] = "false"
                content.append(tx)
                print("new block added, count is", len(content))
                dic[tx["hash"]] = len(content) - 1
        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='CDB-Net: Decentralized '
                                 'CBD Producing Tracking',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/download',methods=['GET'])
def download():
    #把chain写进md文件
    print ("download")
    fo = open("backup_chain.md", "w") 
    fo.write(str(get_chain(CONNECTED_NODE_ADDRESS + '/chain')))
    fo.close()
    directory=os.getcwd()
    return send_from_directory(directory, 'backup_chain.md', as_attachment=True)
    #return redirect('/')


@app.route('/search',methods=['POST'])
def search(): 
    #search function
    hash_number = request.form["search_hash"]
    product_history = []
    del_list=[]
    product_ID=""
    #hash_number = "1d07f47ce9b7b772e4b3c6dfe3e97d2ddd218d1d47f986e12fe3a4d8eb73be15"
    print(hash_number)
    blocks = get_chain(CONNECTED_NODE_ADDRESS + '/chain')
#    for block in blocks:
 #       if block['transactions']!=[]:
  #          if block['transactions'][0]['del_hash'] != '':
   #             del_list.append(block['transactions'][0]['del_hash'])
    for block in blocks:
        if block['hash'] == hash_number:
            product_ID = block['transactions'][0]['grass_ID']
            break
    for block in blocks:
        if block['transactions']!=[]:
            if block['transactions'][0]['grass_ID'] == product_ID and block['hash'] not in del_list:
                product_history.append(block['transactions'])
    print(len(product_history),product_ID)
    return str(product_history)

@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    delete_hash = request.form["del_hash"]
    post_content = request.form["content"]
    author = request.form["author"]
    quantity = request.form["quantity"]
    date = request.form["date"]

    if delete_hash != "":
        post_object = {
            'del_hash': delete_hash
        }
        print('do delete', post_object)
    else:
        print('do not delete',delete_hash)
        if author == "Farm":
            global grass_ID
            grass_ID += 1
        else:
            grass_ID = int(request.form["grass_ID"])

        post_object = {
            'date': date,
            'grass_ID': grass_ID,
            'author': author,
            'content': post_content,
            'quantity': quantity,
    #       'del_hash': delete_hash
        }

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})
    #auto mining the transaction block after submit
    miner_url = CONNECTED_NODE_ADDRESS + "/mine"
    auto_miner(miner_url)
    return redirect('/')


#mine latest block
def auto_miner(url_mine):
    miner=requests.get(url_mine)
    print("auto miner working:",miner.status_code," ",miner.content)

#get the whole chain data
def get_chain(url_chain):
    chain = requests.get(url_chain)
    if chain.status_code == 200: #把chain.content改成Jason文件，按时间顺序排列
        chain_file=chain.content
        my_json = (chain.content).decode('utf8').replace("'", '"')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        data = json.loads(my_json)
        return (data['chain'])
    else:
        return False

#tiimestamp to string
def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%D %H:%M:%S')
