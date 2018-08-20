import webbrowser
import requests
import json
from flask import Flask, render_template, request

app = Flask(__name__)
base_url = "https://apiv2.twitcasting.tv"

class Credentials:
    # APIキーの指定
    with open ('./credentials/clientid', 'r') as f:
        client_id = f.read()
    with open ('./credentials/clientsecret', 'r') as f:
        client_secret = f.read()
    code = ""
    access_token = ""
    headers = ""
    
def get_oauth():
    # APIのひな型
    api = "https://apiv2.twitcasting.tv/oauth2/authorize?client_id={YOUR_CLINET_ID}&response_type=code"

    url = api.format(YOUR_CLINET_ID=Credentials.client_id)
    webbrowser.open(url)

def get_headers():
    params = {
        'code' : Credentials.code,
        'grant_type' : "authorization_code",
        'client_id' : Credentials.client_id,
        'client_secret' : Credentials.client_secret,
        'redirect_uri' : "http://localhost:8080"
    }
    url = "https://apiv2.twitcasting.tv/oauth2/access_token"

    r = requests.post(url, params)

    data = json.loads(r.text)

    headers = {
        'Authorization' : "Bearer " + data["access_token"],
        'X-Api-Version' : "2.0"
    }
    Credentials.headers = headers


def get_current_movie_info_from_user_id(user_id):
    r = requests.get(base_url + "/users/{user_id}".format(user_id=user_id), headers=headers)
    data = json.loads(r.text)
    if data['user']['is_live']:
        print('living...')
        r = requests.get(base_url + "/users/{user_id}/current_live".format(user_id=user_id), headers=headers)
        current_live = json.loads(r.text)
        return current_live['movie']
    else:
        print('offline.')
        return None

def get_last_comment(movie_id):
    r = requests.get(base_url + "/movies/{movie_id}/comments".format(movie_id=movie_id), headers=headers, params={'limit' : 1})
    res = json.loads(r.text)
    if res['all_count'] == 0:
        print("no comments.")
        tail = "*"
    else:
        tail = res['comments'][0]['message']
    return tail

def post_comment(movie_id, comment):
    params = {
         'comment' : comment
    }
    r = requests.post(base_url + "/movies/{movie_id}/comments".format(movie_id=movie_id), headers=headers, data=json.dumps(params))
    res = json.loads(r.text)
    return res

def post_comment_with_shiritori(movie_id, comment):
    import MeCab
    
    last_comment = get_last_comment(movie_id)
    print("----- しりとり判定 -----")
    print("last comment : {0}".format(last_comment))
    print("your comment : {0}".format(comment))

    
    if last_comment == "*":
        print("----- しりとり開始 -----")
        return post_comment(movie_id, comment)
    elif text2kana(last_comment)[-1] != text2kana(comment)[0]:
        print("----- しりとり不成立 -----")
        return None
    else:
        print("----- しりとり成立 -----")
        return post_comment(movie_id, comment)

def text2kana(string):
    import MeCab
    import re

    mecab = MeCab.Tagger('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
    node = mecab.parseToNode(string)
    text = []
    while node:
        if node.feature.split(",")[6] == '*':
            word = node.surface
        elif re.match("[ァ-ヴ]",node.feature.split(",")[7]):
            text.append(node.feature.split(",")[7])
        node = node.next
    return "".join(text)

@app.route('/')
def index():
    # 「templates/index.html」のテンプレートを使う
    # 「message」という変数に"Hello"と代入した状態で、テンプレート内で使う
    code = request.args.get('code', '')
    Credentials.code = code
    get_headers()
    return render_template('index.html', message="ok")

@app.route('/test')
def test():
    return render_template('test.html', message="test")


if __name__ == "__main__":
    get_oauth()
    app.run(port=8080)