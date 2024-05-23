import os
import json
import logging
from urllib import request, error
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

chatgpt_url = "https://api.openai.com/v1/chat/completions"

# 設定系 (お好みで)
TEMPERATURE = 0.5
MAX_TOKENS = 2048
N = 1
TOP_P = 1
presence_penalty = 0.6
frequency_penalty = 0.0

system_role_defile="""
(お好きなロール設定を記載)
"""

def ask_chatgpt(prompt):

    api_key = os.environ["OPENAI_API_KEY"]

    model = os.environ["MODEL"]
    url = chatgpt_url

    output_text = ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_role_defile},
            {"role": "user", "content": prompt}
        ],
        "model": model,
        "n": N,
        "top_p": TOP_P,
        "temperature": TEMPERATURE
    }

    logger.info(f"url:{url}")
    logger.info(f"headers:{headers}")
    logger.info(f"payload:{payload}")
    req = request.Request(url, json.dumps(payload).encode(), headers, method="POST")

    try:
        with request.urlopen(req) as res:
            logger.info(f"status: {res.status} headers: {res.headers} msg: {res.msg}")
            response = json.loads(res.read().decode('utf-8'))

            logger.info(response)

            output_text = response['choices'][0]['message']['content'].strip()

    except error.HTTPError as e:
        logger.error(f"HTTPErrorが発生しました:{e}")
        if e.code == 429:
            output_text = f"申し訳ありません。429エラー({str(e)}) が発生しました。時間を置いて再度メッセージを送ってください。"
        else:
            output_text = str(e)
    except Exception as e:
        logger.error(f"想定外のエラーが発生しました:{e}")
        output_text = f"申し訳ありません。エラー({str(e)}) が発生しました。"

    return output_text


def reply_to_slack(channel, message, thread_ts=""):
    headers = { 'Content-Type': 'application/json; charset=utf-8' }

    url = os.environ["SLACK_WEBHOOK_URL"]

    if not message:
        message = "No Text"
    payload = {
        'text': message,
        "channel": channel,
        "icon_emoji": "",
        "thread_ts": thread_ts,
    }

    logger.info(f"Header: {headers} Payload: {payload}")

    req = request.Request(url, json.dumps(payload).encode("utf-8"), headers, method='POST')

    with request.urlopen(req) as res:
        logger.info(f"status: {res.status} headers: {res.headers} msg: {res.msg}")



def remove_at_symbol(string):
    return re.sub(r'<@.*?>', '', string)


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    body = {}
    if event.get('body'):
        body = json.loads(event['body'])

    if event.get('headers', {}).get('x-slack-signature'):
        # Slack からのアクセス時のみ対応
        channel = body['event']['channel']

        # メンション部分を削除
        text_args = body['event']['text']
        prompt = remove_at_symbol(text_args)

        logger.info(f"プロンプト: {prompt}")

        res = ask_chatgpt(prompt)

        thread_ts = body['event']['ts']

        logger.info(f"channel:{channel}, thread_ts:{thread_ts}")
        logger.info(f"res:{res}")

        reply_to_slack(channel, res, thread_ts)
    else:
        logger.info(f"Slackからの投稿ではないため終了します。")
