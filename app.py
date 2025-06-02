from flask import Flask, request, jsonify
import requests
import os
from requests_oauthlib import OAuth1
import logging

app = Flask(__name__)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数から認証情報を取得
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# OAuth1認証の設定
auth = OAuth1(
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)

@app.route('/')
def home():
    return jsonify({"status": "Twitter Bridge Server is running!"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/tweet', methods=['POST'])
def post_tweet():
    try:
        # リクエストからツイート内容を取得
        data = request.get_json()
        tweet_text = data.get('text')
        
        if not tweet_text:
            return jsonify({"error": "No text provided"}), 400
        
        # Twitter APIエンドポイント
        url = "https://api.twitter.com/2/tweets"
        
        # ツイートデータ
        payload = {"text": tweet_text}
        
        # APIリクエスト
        response = requests.post(
            url,
            json=payload,
            auth=auth
        )
        
        # レスポンス処理
        if response.status_code == 201:
            logger.info(f"Tweet posted successfully: {tweet_text[:50]}...")
            return jsonify({
                "status": "success",
                "data": response.json()
            })
        else:
            logger.error(f"Failed to post tweet: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Failed to post tweet",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error in post_tweet: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/timeline', methods=['GET'])
def get_timeline():
    try:
        # ユーザーIDを環境変数から取得（事前に設定が必要）
        user_id = os.environ.get('TWITTER_USER_ID')
        if not user_id:
            return jsonify({"error": "User ID not configured"}), 500
        
        # タイムライン取得エンドポイント
        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        
        # パラメータ設定
        params = {
            'max_results': 10,  # 最新10件
            'tweet.fields': 'created_at,text'
        }
        
        # APIリクエスト
        response = requests.get(
            url,
            params=params,
            auth=auth
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "data": response.json()
            })
        else:
            return jsonify({
                "error": "Failed to get timeline",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error in get_timeline: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Renderで実行時はポート番号を環境変数から取得
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
