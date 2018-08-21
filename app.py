import webbrowser
import requests
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
base_url = "https://apiv2.twitcasting.tv"
class info:
    user_name=""
    movie_id=""


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
    r = requests.get(base_url + "/users/{user_id}".format(user_id=user_id), headers=Credentials.headers)
    data = json.loads(r.text)
    if data['user']['is_live']:
        print('living...')
        r = requests.get(base_url + "/users/{user_id}/current_live".format(user_id=user_id), headers=Credentials.headers)
        current_live = json.loads(r.text)
        return current_live['movie']
    else:
        print('offline.')
        return None

def get_last_comment(movie_id):
    r = requests.get(base_url + "/movies/{movie_id}/comments".format(movie_id=movie_id), headers=Credentials.headers, params={'limit' : 1})
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
    r = requests.post(base_url + "/movies/{movie_id}/comments".format(movie_id=movie_id), headers=Credentials.headers, data=json.dumps(params))
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
    
    tail = text2kana(last_comment)[-1]
    head = text2kana(comment)[0]
    tail = small2big_kana(tail)
    
    if tail != head:
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

def small2big_kana(kana):
    if kana == "ァ":
        kana = "ア"
    elif kana == "ィ":
        kana = "イ"
    elif kana == "ゥ":
        kana = "ウ"
    elif kana == "ェ":
        kana = "エ"
    elif kana == "ォ":
        kana = "オ"
    elif kana == "ャ":
        kana = "ヤ"
    elif kana == "ュ":
        kana = "ユ"
    elif kana == "ョ":
        kana = "ヨ"
    else:
        pass
    return kana


@app.route('/')
def index():
    code = request.args.get('code', '')
    if code != '':
        Credentials.code = code
        get_headers()
        message = "ok"
        return redirect(url_for('form'))
    else:
        message="ng"
    return render_template('index.html', message=message)

@app.route('/test')
def test():
    return render_template('test.html', message="test")

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/confirm', methods = ['POST', 'GET'])
def confirm():
    if request.method == 'POST':
        info.user_name = request.form['user_name']
    movie_info = get_current_movie_info_from_user_id(info.user_name)
    if movie_info is not None:
        message = "放送してるよ"
        info.movie_id = movie_info['id']            
        title = movie_info['title']
        comment_count = movie_info['comment_count']
        last_comment = get_last_comment(info.movie_id)
    else:
        message = "放送してないよ"
        title = "*"
        comment_count = "*"
        last_comment = "*"

    iframe = '<iframe src="https://twitcasting.tv/{0}/embeddedplayer/live?auto_play=true&default_mute=true" width="640px" height="360px" frameborder="0" allowfullscreen></iframe>'.format(info.user_name)
            
    return render_template("confirm.html", user_name=info.user_name, message=message, title=title, comment_count=comment_count, last_comment=last_comment, iframe=iframe)

@app.route('/sent', methods = ['POST'])
def sent():
    comment = request.form['comment']
    last_comment = get_last_comment(info.movie_id)
    res = post_comment_with_shiritori(info.movie_id, comment)
    if res is not None:
        result = "しりとり成立"
    else:
        result = "しりとり不成立"
    return render_template("sent.html", result=result, comment=comment, last_comment=last_comment)
    

    

"""
URLを変数でも指定できるが、よく分かってないんで当分はconfirmのほうを使いそう
"""
"""
@app.route('/<user_name>', methods = ['POST', 'GET'])
def user_name(user_name):
    movie_info = get_current_movie_info_from_user_id(user_name)
    if movie_info is not None:
        message = "放送してるよ"
        title = movie_info['title']
        comment_count = movie_info['comment_count']
        last_comment = get_last_comment(movie_info['id'])
    else:
        message = "放送してないよ"
        title = "*"
        comment_count = "*"
        last_comment = "*"

    return render_template("confirm.html", user_name=user_name, message=message, title=title, comment_count=comment_count, last_comment=last_comment)
"""

if __name__ == "__main__":
    get_oauth()
    app.run(port=8080)
