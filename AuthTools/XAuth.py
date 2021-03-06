# -*- coding: utf-8 -*-

"""
アカウントのアクセストークンとアクセストークンシークレットを xAuth で取得するファイル
"""
import base64
import os
import oauth2
import urllib.parse

from TwitterAPI import TwitterAPI


class TwitterXAuth:

    def __init__(self):

        # Windows 環境向けの hack
        # 参考: https://stackoverflow.com/questions/31469707/changing-the-locale-preferred-encoding-in-python-3-in-windows
        if os.name == 'nt':
            import _locale
            _locale._getdefaultlocale_backup = _locale._getdefaultlocale
            _locale._getdefaultlocale = (lambda *args: (_locale._getdefaultlocale_backup()[0], 'UTF-8'))

        # Twitter API の各種キーを取得
        encoded = [
            b'M25WdVNvQlpueDZVNHZ6VXhmNXc=',
            b'QmNzNTlFRmJic2RGNlNsOU5nNzFzbWdTdFdFR3dYWEtTall2UFZ0N3F5cw==']
        self.consumer_key = base64.standard_b64decode(encoded[0]).decode()
        self.consumer_secret = base64.standard_b64decode(encoded[1]).decode()

        # 各種キーのいずれかが取得できなかったらエラー
        if self.consumer_key is None or self.consumer_secret is None:
            raise Exception('The Twitter API consumer key or access token has not been set.')

    def xauth(self, screen_name, password, endpoint='https://api.twitter.com/oauth/access_token'):
        """
        スクリーンネームとパスワードで xAuth を行う
        参考: https://github.com/yuitest/twitterxauth/blob/master/twitterxauth/__init__.py
        @param screen_name スクリーンネーム
        @param password パスワード
        @return アクセストークンとアクセストークンシークレットのタプル
        """

        # ヘッダーを設定
        headers = TwitterAPI.generate_header(self.consumer_key)
        print(headers)

        # OAuth2 認証
        consumer = oauth2.Consumer(self.consumer_key, self.consumer_secret)
        client = oauth2.Client(consumer)
        client.add_credentials(screen_name, password)
        client.set_signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        response, token = client.request(
            endpoint, method='POST', headers=headers, body=urllib.parse.urlencode({
                'x_auth_mode': 'client_auth',
                'x_auth_username': screen_name,
                'x_auth_password': password,
            }))

        # 返ってきたメッセージを解析
        parsed_token = dict(urllib.parse.parse_qsl(token.decode('UTF-8')))
        if parsed_token == {}:  # parse_token が空 → 認証に失敗したので例外を投げる
            raise Exception(token.decode('UTF-8'))

        return parsed_token['oauth_token'], parsed_token['oauth_token_secret']


if __name__ == '__main__':
    # 初期化
    instance = TwitterXAuth()

    # スクリーンネームを取得
    screen_name = input('Screen name: ')

    # パスワードを取得
    password = input('Password: ')

    # xAuth を実行
    access_token, access_token_secret = instance.xauth(screen_name, password)

    # アクセストークンとアクセストークンシークレットを表示
    print('Access token       : ' + access_token)
    print('Access token secret: ' + access_token_secret)
