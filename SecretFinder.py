#!/usr/bin/env python
# SecretFinder - Tool for discover apikeys/accesstokens and sensitive data in js file
# based on LinkFinder - github.com/GerbenJavado
# By m4ll0k (@m4ll0k2) github.com/m4ll0k


import os,sys
if not sys.version_info.major >= 3:
    print("[ + ] Run this tool with python version 3.+")
    sys.exit(0)
os.environ["BROWSER"] = "open"

import re
import glob
import argparse
import jsbeautifier
import webbrowser
import subprocess
import base64
import requests
import string
import random
from html import escape
import urllib3
import xml.etree.ElementTree

# disable warning

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# for read local file with file:// protocol
from requests_file import FileAdapter
from lxml import html
from urllib.parse import urlparse

# regex
_regex = {
    'google_api'     : r'AIza[0-9A-Za-z-_]{35}',
    'firebase'  : r'AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}',
    'google_captcha' : r'6L[0-9A-Za-z-_]{38}|^6[0-9a-zA-Z_-]{39}$',
    'google_oauth'   : r'ya29\.[0-9A-Za-z\-_]+',
    'amazon_aws_access_key_id' : r'A[SK]IA[0-9A-Z]{16}',
    'amazon_mws_auth_toke' : r'amzn\\.mws\\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    'amazon_aws_url' : r's3\.amazonaws.com[/]+|[a-zA-Z0-9_-]*\.s3\.amazonaws.com',
    'amazon_aws_url2' : r"(" \
           r"[a-zA-Z0-9-\.\_]+\.s3\.amazonaws\.com" \
           r"|s3://[a-zA-Z0-9-\.\_]+" \
           r"|s3-[a-zA-Z0-9-\.\_\/]+" \
           r"|s3.amazonaws.com/[a-zA-Z0-9-\.\_]+" \
           r"|s3.console.aws.amazon.com/s3/buckets/[a-zA-Z0-9-\.\_]+)",
    'facebook_access_token' : r'EAACEdEose0cBA[0-9A-Za-z]+',
    'authorization_basic' : r'basic [a-zA-Z0-9=:_\+\/-]{5,100}',
    'authorization_bearer' : r'bearer [a-zA-Z0-9_\-\.=:_\+\/]{5,100}',
    'authorization_api' : r'api[key|_key|\s+]+[a-zA-Z0-9_\-]{5,100}',
    'mailgun_api_key' : r'key-[0-9a-zA-Z]{32}',
    'twilio_api_key' : r'SK[0-9a-fA-F]{32}',
    'twilio_account_sid' : r'AC[a-zA-Z0-9_\-]{32}',
    'twilio_app_sid' : r'AP[a-zA-Z0-9_\-]{32}',
    'paypal_braintree_access_token' : r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
    'square_oauth_secret' : r'sq0csp-[ 0-9A-Za-z\-_]{43}|sq0[a-z]{3}-[0-9A-Za-z\-_]{22,43}',
    'square_access_token' : r'sqOatp-[0-9A-Za-z\-_]{22}|EAAA[a-zA-Z0-9]{60}',
    'stripe_standard_api' : r'sk_live_[0-9a-zA-Z]{24}',
    'stripe_restricted_api' : r'rk_live_[0-9a-zA-Z]{24}',
    'github_access_token' : r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_\-]+@github\.com*',
    'rsa_private_key' : r'-----BEGIN RSA PRIVATE KEY-----',
    'ssh_dsa_private_key' : r'-----BEGIN DSA PRIVATE KEY-----',
    'ssh_dc_private_key' : r'-----BEGIN EC PRIVATE KEY-----',
    'pgp_private_block' : r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
    'json_web_token' : r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$',
    'slack_token' : r"\"api_token\":\"(xox[a-zA-Z]-[a-zA-Z0-9-]+)\"",
    'SSH_privKey' : r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)",
    'Heroku API KEY' : r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
    'possible_Creds' : r"(?i)(" \
                    r"password\s*[`=:\"]+\s*[^\s]+|" \
                    r"password is\s*[`=:\"]*\s*[^\s]+|" \
                    r"pwd\s*[`=:\"]*\s*[^\s]+|" \
                    r"passwd\s*[`=:\"]+\s*[^\s]+)",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?server[_-]?api[_-]?key[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?partner[_-]?refresh[_-]?token[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?partner[_-]?client[_-]?secret[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?client[_-]?secret[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?api[_-]?key[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?account[_-]?refresh[_-]?token[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yt[_-]?account[_-]?client[_-]?secret[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yangshun[_-]?gh[_-]?token[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?yangshun[_-]?gh[_-]?password[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?www[_-]?googleapis[_-]?com[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r"(?i)[\"']?wpt[_-]?ssh[_-]?private[_-]?key[_-]?base64[\"']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"']?[\\w-]+[\"']?",
    "Possible Leak" : r'(?i)["\']?bundlesize[_-]?github[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?built[_-]?branch[_-]?deploy[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bucketeer[_-]?aws[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bucketeer[_-]?aws[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?browserstack[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?browser[_-]?stack[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?brackets[_-]?repo[_-]?oauth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?username["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?pwd["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?pass[_-]?prod["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?repo[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?release[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?pwd[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?password[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?oauth[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?oauth[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?key[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?hunter[_-]?username[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?hunter[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?github[_-]?deployment[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?argos[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?apple[_-]?id[_-]?password[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?appclientsecret[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?app[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?app[_-]?secrete[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?app[_-]?report[_-]?token[_-]?key[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?app[_-]?bucket[_-]?perm[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?apigw[_-]?access[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?apiary[_-]?api[_-]?key[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?api[_-]?secret[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?api[_-]?key[_-]?sid[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?api[_-]?key[_-]?secret[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?api[_-]?key[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?aos[_-]?sec[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?aos[_-]?key[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?ansible[_-]?vault[_-]?password[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)[\"\']?android[_-]?docs[_-]?deploy[_-]?token[\"\']?\s*[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?ses[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secrets["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?config[_-]?secretaccesskey["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?config[_-]?accesskeyid["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?access["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?author[_-]?npm[_-]?api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?author[_-]?email[_-]?addr["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?auth0[_-]?client[_-]?secret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?auth0[_-]?api[_-]?clientsecret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?auth[_-]?token["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?assistant[_-]?iam[_-]?apikey["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifacts[_-]?secret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifacts[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifacts[_-]?bucket["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifacts[_-]?aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifacts[_-]?aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?artifactory[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?argos[_-]?token["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?apple[_-]?id[_-]?password["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?appclientsecret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?app[_-]?token["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?app[_-]?secrete["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?app[_-]?report[_-]?token[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?app[_-]?bucket[_-]?perm["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?apigw[_-]?access[_-]?token["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?apiary[_-]?api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?api[_-]?secret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?api[_-]?key[_-]?sid["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?api[_-]?key[_-]?secret["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aos[_-]?sec["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aos[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ansible[_-]?vault[_-]?password["\']?\s*[:=]\s*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?consumerkey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?consumer[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?conekta[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?coding[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?codecov[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?codeclimate[_-]?repo[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?codacy[_-]?project[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cocoapods[_-]?trunk[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cocoapods[_-]?trunk[_-]?email["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cn[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cn[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?clu[_-]?ssh[_-]?private[_-]?key[_-]?base64["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?clu[_-]?repo[_-]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudinary[_-]?url[_-]?staging["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudinary[_-]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudflare[_-]?email["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudflare[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudflare[_-]?auth[_-]?email["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudflare[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?service[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?processed[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?parsed[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?order[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?instance["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?audited[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloudant[_-]?archived[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cloud[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?clojars[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?client[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cli[_-]?e2e[_-]?cma[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?claimr[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?claimr[_-]?superuser["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?claimr[_-]?db["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?claimr[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ci[_-]?user[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ci[_-]?server[_-]?name["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ci[_-]?registry[_-]?user["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ci[_-]?project[_-]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ci[_-]?deploy[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?chrome[_-]?refresh[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?chrome[_-]?client[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cheverny[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cf[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?certificate[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?censys[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cattle[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cattle[_-]?agent[_-]?instance[_-]?auth["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cattle[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cargo[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?cache[_-]?s3[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bx[_-]?username["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bx[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bundlesize[_-]?github[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?built[_-]?branch[_-]?deploy[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bucketeer[_-]?aws[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bucketeer[_-]?aws[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?browserstack[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?browser[_-]?stack[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?brackets[_-]?repo[_-]?oauth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?username["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?pwd["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?pass[_-]?prod["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?pass["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?auth["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bluemix[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintraykey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintray[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintray[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintray[_-]?gpg[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintray[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?bintray[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?b2[_-]?bucket["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?b2[_-]?app[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?awssecretkey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?awscn[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?awscn[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?awsaccesskeyid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?ses[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gh[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gcs[_-]?bucket[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gcr[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gcloud[_-]?service[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gcloud[_-]?project[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?gcloud[_-]?bucket[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?username[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?user[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?pw[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?login[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?ftp[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?fossa[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?flickr[_-]?api[_-]?secret[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?flickr[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?flask[_-]?secret[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firefox[_-]?secret[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firebase[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firebase[_-]?project[_-]?develop[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firebase[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firebase[_-]?api[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?firebase[_-]?api[_-]?json[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?file[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?exp[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?eureka[_-]?awssecretkey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?sonatype[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?secret[_-]?access[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?secret[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?heroku[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?env[_-]?github[_-]?oauth[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?end[_-]?user[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?encryption[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?elasticsearch[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?elastic[_-]?cloud[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dsonar[_-]?projectkey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dsonar[_-]?login[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dsonar[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dsonar[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dotenv[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digicert[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digicert[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digitalocean[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digital[_-]?ocean[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digital[_-]?ocean[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?digital[_-]?ocean[_-]?access[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?devtools[_-]?honeycomb[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?tools[_-]?honeycomb[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?to[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rake[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?login[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?admin[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?admin[_-]?login[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?rabbitmq[_-]?admin[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?postgres[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?postgres[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?mysql[_-]?password[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?mysql[_-]?host[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?api[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?credentials[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?code[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?token[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?token[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?key[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?key[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?id[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?access[_-]?credential[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?secret[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?key[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?credentials[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?auth[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?access[_-]?token[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?access[_-]?id[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?key[_-]?id[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?auth[_-]?token[_-]?key[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?auth[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?apikey[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?token[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?id[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)[\"\'\']?dev[_-]?microsoft[_-]?account[_-]?apikey[_-]?key[_-]?auth[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?access[_-]?credential[\"\'\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\'\']?[\\w-]+[\"\'\']?',
    "Possible Leak" : r'(?i)["\']?netlify[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?nativeevents["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysqlsecret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysqlmasteruser["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?username["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?user["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?root[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?hostname["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mysql[_-]?database["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?my[_-]?secret[_-]?env["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?multi[_-]?workspace[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?multi[_-]?workflow[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?multi[_-]?disconnect[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?multi[_-]?connect[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?multi[_-]?bob[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?minio[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?minio[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mile[_-]?zero[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mh[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mh[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mg[_-]?public[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mg[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mapboxaccesstoken["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mapbox[_-]?aws[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mapbox[_-]?aws[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mapbox[_-]?api[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mapbox[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?manifest[_-]?app[_-]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?manifest[_-]?app[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mandrill[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?managementapiaccesstoken["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?management[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?manage[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?manage[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?secret[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?pub[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?sender[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?sender[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mail[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?link[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magento[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magento[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magento[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magento[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?secret[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?magic[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?pub["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?priv["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?access[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?api[_-]?key[_-]?access[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?access[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailgun[_-]?access[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?pub["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?priv["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?access[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?apikey[_-]?access[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?access[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailchimp[_-]?access[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailer[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailer[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailer[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailer[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?mailer[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?api[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?access[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?project[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?client[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?client[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?secret[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?private[_-]?key[_-]?secret[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?public[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?project[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?project[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?service[_-]?account[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?amazon[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?aws[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?azure[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?github[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?gitlab[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?linkedin[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?microsoft[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?facebook[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?twitter[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?auth[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?google[_-]?token[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?auth[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?pub[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?secret[_-]?api[_-]?key[_-]?priv[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?token[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?token[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?token[_-]?api[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?token[_-]?api[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?youtube[_-]?token[_-]?api[_-]?key[_-]?apikey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?sandbox[-_]?access[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?salesforce[-_]?bulk[-_]?test[-_]?security[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?salesforce[-_]?bulk[-_]?test[-_]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?sacloud[-_]?api["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?sacloud[-_]?access[-_]?token[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?sacloud[-_]?access[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?user[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?secret[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?secret[-_]?assets["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?secret[-_]?app[-_]?logs["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?key[-_]?assets["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?key[-_]?app[-_]?logs["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?external[-_]?3[-_]?amazonaws[-_]?com["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?bucket[-_]?name[-_]?assets["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?bucket[-_]?name[-_]?app[-_]?logs["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?access[-_]?key[-_]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?s3[-_]?access[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?rubygems[-_]?auth[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?rtd[-_]?store[-_]?pass["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?rtd[-_]?key[-_]?pass["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?route53[-_]?access[-_]?key[-_]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?ropsten[-_]?private[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?rinkeby[-_]?private[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?rest[-_]?api[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak" : r'(?i)["\']?repotoken["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?reporting[-_]?webdav[-_]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?reporting[-_]?webdav[-_]?pwd["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?release[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?release[-_]?gh[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?registry[-_]?secure["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?registry[-_]?pass["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?refresh[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?rediscloud[-_]?url["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?redis[-_]?stunnel[-_]?urls["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?randrmusicapiaccesstoken["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?rabbitmq[-_]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?quip[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?qiita[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pypi[-_]?passowrd["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pushover[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pushover[-_]?user["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pusher[-_]?app[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pubnub[-_]?subscribe[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pubnub[-_]?secret[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pubnub[-_]?publish[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pubnub[-_]?cipher[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pubnub[-_]?auth[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?prometheus[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?private[-_]?key[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?prismic[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?private[-_]?key[-_]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?project[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?prod[-_]?deploy[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?private[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?pivotal[-_]?tracker[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?personal[-_]?access[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?paypal[-_]?client[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?paypal[-_]?client[-_]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?path[-_]?to[-_]?file["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?passwd[-_]?s3[-_]?access[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?passwd[-_]?s3[-_]?secret[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?to[-_]?jenkins["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?to[-_]?file["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?to[-_]?azure[-_]?file["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?test["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?storj["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?staging["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?stage["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?slack["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?s3["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?repo["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?rds["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?postgres["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?private["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?prod["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?preview["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?pypi["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?publish["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?qld["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?pub["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?priv["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?prod[-_]?private["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?pr["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?preprod["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?preprod[-_]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?pr[-_]?live["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?p4["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?p2["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?p1["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?p[-_]?mail["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?p["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?os[-_]?aerogear["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?opensource["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?oauth["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?oauth[-_]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?o["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?myweb["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?mygit["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?my[-_]?github["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?my[-_]?git["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?migrations["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?mc4["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jwt["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jira["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?user["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?service["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?master["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?domain["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?deploy["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?admin["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins[-_]?01["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-123["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-01["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-0000["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-000["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-12345["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-0012345["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-001234["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-00123["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-0012345["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-00123["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00000["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-0000["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-000["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-0["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-0["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-00["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-001["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-002["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-003["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-004["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?password[-_]?jenkins-004["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?snoowrap[_-]?refresh[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?snoowrap[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?snoowrap[_-]?client[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?slate[_-]?user[_-]?email["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?slash[_-]?developer[_-]?space[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?slash[_-]?developer[_-]?space["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?signing[_-]?key[_-]?sid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?signing[_-]?key[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?signing[_-]?key[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?signing[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?setsecretkey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?setdstsecretkey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?setdstaccesskey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?ses[_-]?secret[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?ses[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?service[_-]?account[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sentry[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sentry[_-]?secret["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sentry[_-]?endpoint["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sentry[_-]?default[_-]?org["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sentry[_-]?auth[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendwithus[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid[_-]?username["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid[_-]?user["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid[_-]?password["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sendgrid["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?selion[_-]?selenium[_-]?host["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?selion[_-]?log[_-]?level[_-]?dev["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?segment[_-]?api[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secretkey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secretaccesskey["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?key[_-]?base["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?9["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?8["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?7["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?6["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?5["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?4["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?3["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?2["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?11["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?10["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?1["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?secret[_-]?0["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sdr[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?scrutinizer[_-]?token["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sauce[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sandbox[_-]?aws[_-]?secret[_-]?access[_-]?key["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)["\']?sandbox[_-]?aws[_-]?access[_-]?key[_-]?id["\']?[^\\S\r\n]*[=:][^\\S\r\n]*["\']?[\w-]+["\']?',
    "Possible Leak " : r'(?i)[\"\']?twine[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?sid[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?configuration[_-]?sid[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?chat[_-]?account[_-]?api[_-]?service[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?api[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twilio[_-]?api[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?trex[_-]?okta[_-]?client[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?trex[_-]?client[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?secure[_-]?env[_-]?vars[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?pull[_-]?request[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?gh[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?e2e[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?com[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?branch[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?api[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?travis[_-]?access[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?token[_-]?core[_-]?java[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?thera[_-]?oss[_-]?access[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?tester[_-]?keys[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?test[_-]?test[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?test[_-]?github[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?tesco[_-]?api[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?svn[_-]?pass[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?surge[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?surge[_-]?login[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?stripe[_-]?public[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?stripe[_-]?private[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?strip[_-]?secret[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?strip[_-]?publishable[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?stormpath[_-]?api[_-]?key[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?stormpath[_-]?api[_-]?key[_-]?id[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?starship[_-]?auth[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?starship[_-]?account[_-]?sid[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?star[_-]?test[_-]?secret[_-]?access[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?star[_-]?test[_-]?location[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?star[_-]?test[_-]?bucket[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?star[_-]?test[_-]?aws[_-]?access[_-]?key[_-]?id[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?staging[_-]?base[_-]?url[_-]?runscope[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?ssmtp[_-]?config[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sshpass[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?srcclr[_-]?api[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?square[_-]?reader[_-]?sdk[_-]?repository[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sqssecretkey[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sqsaccesskey[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?spring[_-]?mail[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?spotify[_-]?api[_-]?client[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?spotify[_-]?api[_-]?access[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?spaces[_-]?secret[_-]?access[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?spaces[_-]?access[_-]?key[_-]?id[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?soundcloud[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?soundcloud[_-]?client[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatypepassword[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?token[_-]?user[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?token[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?pass[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?nexus[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?gpg[_-]?passphrase[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonatype[_-]?gpg[_-]?key[_-]?name[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonar[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonar[_-]?project[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?sonar[_-]?organization[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?socrata[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?socrata[_-]?app[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?snyk[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?snyk[_-]?api[_-]?token[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?wpjm[_-]?phpunit[_-]?google[_-]?geocode[_-]?api[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?wordpress[_-]?db[_-]?user[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?wordpress[_-]?db[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?wincert[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?test[_-]?server[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?fb[_-]?password[_-]?3[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?fb[_-]?password[_-]?2[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?fb[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?basic[_-]?password[_-]?5[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?basic[_-]?password[_-]?4[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?basic[_-]?password[_-]?3[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?basic[_-]?password[_-]?2[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?widget[_-]?basic[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?watson[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?watson[_-]?device[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?watson[_-]?conversation[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?wakatime[_-]?api[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?vscetoken[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?visual[_-]?recognition[_-]?api[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?virustotal[_-]?apikey[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?vip[_-]?github[_-]?deploy[_-]?key[_-]?pass[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?vip[_-]?github[_-]?deploy[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?vip[_-]?github[_-]?build[_-]?repo[_-]?deploy[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?v[_-]?sfdc[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?v[_-]?sfdc[_-]?client[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?usertravis[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?user[_-]?assets[_-]?secret[_-]?access[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?user[_-]?assets[_-]?access[_-]?key[_-]?id[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?use[_-]?ssh[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?us[_-]?east[_-]?1[_-]?elb[_-]?amazonaws[_-]?com[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?urban[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?urban[_-]?master[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?urban[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?unity[_-]?serial[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?unity[_-]?password[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twitteroauthaccesstoken[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twitteroauthaccesssecret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twitter[_-]?consumer[_-]?secret[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?',
    "Possible Leak " : r'(?i)[\"\']?twitter[_-]?consumer[_-]?key[\"\']?[^\\S\r\n]*[=:][^\\S\r\n]*[\"\']?[\w-]+[\"\']?'
}

_template = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
       h1 {
          font-family: sans-serif;
       }
       a {
          color: #000;
       }
       .text {
          font-size: 16px;
          font-family: Helvetica, sans-serif;
          color: #323232;
          background-color: white;
       }
       .container {
          background-color: #e9e9e9;
          padding: 10px;
          margin: 10px 0;
          font-family: helvetica;
          font-size: 13px;
          border-width: 1px;
          border-style: solid;
          border-color: #8a8a8a;
          color: #323232;
          margin-bottom: 15px;
       }
       .button {
          padding: 17px 60px;
          margin: 10px 10px 10px 0;
          display: inline-block;
          background-color: #f4f4f4;
          border-radius: .25rem;
          text-decoration: none;
          -webkit-transition: .15s ease-in-out;
          transition: .15s ease-in-out;
          color: #333;
          position: relative;
       }
       .button:hover {
          background-color: #eee;
          text-decoration: none;
       }
       .github-icon {
          line-height: 0;
          position: absolute;
          top: 14px;
          left: 24px;
          opacity: 0.7;
       }
  </style>
  <title>LinkFinder Output</title>
</head>
<body contenteditable="true">
  $$content$$

  <a class='button' contenteditable='false' href='https://github.com/m4ll0k/SecretFinder/issues/new' rel='nofollow noopener noreferrer' target='_blank'><span class='github-icon'><svg height="24" viewbox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg">
  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg></span> Report an issue.</a>
</body>
</html>
'''

def parser_error(msg):
    print('Usage: python %s [OPTIONS] use -h for help'%sys.argv[0])
    print('Error: %s'%msg)
    sys.exit(0)

def getContext(matches,content,name,rex='.+?'):
    ''' get context '''
    items = []
    matches2 =  []
    for  i in [x[0] for x in matches]:
        if i not in matches2:
            matches2.append(i)
    for m in matches2:
        context = re.findall('%s%s%s'%(rex,m,rex),content,re.IGNORECASE)

        item = {
            'matched'          : m,
            'name'             : name,
            'context'          : context,
            'multi_context'    : True if len(context) > 1 else False
        }
        items.append(item)
    return items


def parser_file(content,mode=1,more_regex=None,no_dup=1):
    ''' parser file '''
    if mode == 1:
        if len(content) > 1000000:
            content = content.replace(";",";\r\n").replace(",",",\r\n")
        else:
            content = jsbeautifier.beautify(content)
    all_items = []
    for regex in _regex.items():
        r = re.compile(regex[1],re.VERBOSE|re.I)
        if mode == 1:
            all_matches = [(m.group(0),m.start(0),m.end(0)) for m in re.finditer(r,content)]
            items = getContext(all_matches,content,regex[0])
            if items != []:
                all_items.append(items)
        else:
            items = [{
                'matched' : m.group(0),
                'context' : [],
                'name'    : regex[0],
                'multi_context' : False
            } for m in re.finditer(r,content)]
        if items != []:
            all_items.append(items)
    if all_items != []:
        k = []
        for i in range(len(all_items)):
            for ii in all_items[i]:
                if ii not in k:
                    k.append(ii)
        if k != []:
            all_items = k

    if no_dup:
        all_matched = set()
        no_dup_items = []
        for item in all_items:
            if item != [] and type(item) is dict:
                if item['matched'] not in all_matched:
                    all_matched.add(item['matched'])
                    no_dup_items.append(item)
        all_items = no_dup_items

    filtered_items = []
    if all_items != []:
        for item in all_items:
            if more_regex:
                if re.search(more_regex,item['matched']):
                    filtered_items.append(item)
            else:
                filtered_items.append(item)
    return filtered_items


def parser_input(input):
    ''' Parser Input '''
    # method 1 - url
    schemes = ('http://','https://','ftp://','file://','ftps://')
    if input.startswith(schemes):
        return [input]
    # method 2 - url inpector firefox/chrome
    if input.startswith('view-source:'):
        return [input[12:]]
    # method 3 - Burp file
    if args.burp:
        jsfiles = []
        items = []

        try:
            items = xml.etree.ElementTree.fromstring(open(args.input,'r').read())
        except Exception as err:
            print(err)
            sys.exit()
        for item in items:
            jsfiles.append(
                {
                    'js': base64.b64decode(item.find('response').text).decode('utf-8','replace'),
                    'url': item.find('url').text
                }
            )
        return jsfiles
    # method 4 - folder with a wildcard
    if '*' in input:
        paths = glob.glob(os.path.abspath(input))
        for index, path in enumerate(paths):
            paths[index] = "file://%s" % path
        return (paths if len(paths)> 0 else parser_error('Input with wildcard does not match any files.'))

    # method 5 - local file
    path = "file://%s"% os.path.abspath(input)
    return [path if os.path.exists(input) else parser_error('file could not be found (maybe you forgot to add http/https).')]


def html_save(output):
    ''' html output '''
    hide = os.dup(1)
    os.close(1)
    os.open(os.devnull,os.O_RDWR)
    try:
        text_file = open(args.output,"wb")
        text_file.write(_template.replace('$$content$$',output).encode('utf-8'))
        text_file.close()

        print('URL to access output: file://%s'%os.path.abspath(args.output))
        file = 'file:///%s'%(os.path.abspath(args.output))
        if sys.platform == 'linux' or sys.platform == 'linux2':
            subprocess.call(['xdg-open',file])
        else:
            webbrowser.open(file)
    except Exception as err:
        print('Output can\'t be saved in %s due to exception: %s'%(args.output,err))
    finally:
        os.dup2(hide,1)

def cli_output(matched):
    ''' cli output '''
    for match in matched:
        print(match.get('name')+'\t->\t'+match.get('matched').encode('ascii','ignore').decode('utf-8'))

def urlParser(url):
    ''' urlParser '''
    parse = urlparse(url)
    urlParser.this_root = parse.scheme + '://' + parse.netloc
    urlParser.this_path = parse.scheme + '://' + parse.netloc  + '/' + parse.path

def extractjsurl(content,base_url):
    ''' JS url extract from html page '''
    soup = html.fromstring(content)
    all_src = []
    urlParser(base_url)
    for src in soup.xpath('//script'):
        src = src.xpath('@src')[0] if src.xpath('@src') != [] else []
        if src != []:
            if src.startswith(('http://','https://','ftp://','ftps://')):
                if src not in all_src:
                    all_src.append(src)
            elif src.startswith('//'):
                src = 'http://'+src[2:]
                if src not in all_src:
                    all_src.append(src)
            elif src.startswith('/'):
                src = urlParser.this_root + src
                if src not in all_src:
                    all_src.append(src)
            else:
                src = urlParser.this_path + src
                if src not in all_src:
                    all_src.append(src)
    if args.ignore and all_src != []:
        temp = all_src
        ignore = []
        for i in args.ignore.split(';'):
            for src in all_src:
                if i in src:
                    ignore.append(src)
        if ignore:
            for i in ignore:
                temp.pop(int(temp.index(i)))
        return temp
    if args.only:
        temp = all_src
        only = []
        for i in args.only.split(';'):
            for src in all_src:
                if i in src:
                    only.append(src)
        return only
    return all_src

def send_request(url):
    ''' Send Request '''
    # read local file
    # https://github.com/dashea/requests-file
    if 'file://' in url:
        s = requests.Session()
        s.mount('file://',FileAdapter())
        return s.get(url).content.decode('utf-8','replace')
    # set headers and cookies
    headers = {}
    default_headers = {
        'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept'          : 'text/html, application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language' : 'en-US,en;q=0.8',
        'Accept-Encoding' : 'gzip'
    }
    if args.headers:
        for i in args.header.split('\\n'):
            # replace space and split
            name,value = i.replace(' ','').split(':')
            headers[name] = value
    # add cookies
    if args.cookie:
        headers['Cookie'] = args.cookie

    headers.update(default_headers)
    # proxy
    proxies = {}
    if args.proxy:
        proxies.update({
            'http'  : args.proxy,
            'https' : args.proxy,
            # ftp
        })
    try:
        resp = requests.get(
            url = url,
            verify = False,
            headers = headers,
            proxies = proxies
        )
        return resp.content.decode('utf-8','replace')
    except Exception as err:
        print(err)
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--extract",help="Extract all javascript links located in a page and process it",action="store_true",default=False)
    parser.add_argument("-i","--input",help="Input a: URL, file or folder",required="True",action="store")
    parser.add_argument("-o","--output",help="Where to save the file, including file name. Default: output.html",action="store", default="output.html")
    parser.add_argument("-r","--regex",help="RegEx for filtering purposes against found endpoint (e.g: ^/api/)",action="store")
    parser.add_argument("-b","--burp",help="Support burp exported file",action="store_true")
    parser.add_argument("-c","--cookie",help="Add cookies for authenticated JS files",action="store",default="")
    parser.add_argument("-g","--ignore",help="Ignore js url, if it contain the provided string (string;string2..)",action="store",default="")
    parser.add_argument("-n","--only",help="Process js url, if it contain the provided string (string;string2..)",action="store",default="")
    parser.add_argument("-H","--headers",help="Set headers (\"Name:Value\\nName:Value\")",action="store",default="")
    parser.add_argument("-p","--proxy",help="Set proxy (host:port)",action="store",default="")
    args = parser.parse_args()

    if args.input[-1:] == "/":
        # /aa/ -> /aa
        args.input = args.input[:-1]

    mode = 1
    if args.output == "cli":
        mode = 0
    # add args
    if args.regex:
        # validate regular exp
        try:
            r = re.search(args.regex,''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(10,50))))
        except Exception as e:
            print('your python regex isn\'t valid')
            sys.exit()

        _regex.update({
            'custom_regex' : args.regex
        })

    if args.extract:
        content = send_request(args.input)
        urls = extractjsurl(content,args.input)
    else:
        # convert input to URLs or JS files
        urls = parser_input(args.input)
    # conver URLs to js file
    output = ''
    for url in urls:
        print('[ + ] URL: '+url)
        if not args.burp:
            file = send_request(url)
        else:
            file = url.get('js')
            url = url.get('url')

        matched = parser_file(file,mode)
        if args.output == 'cli':
            cli_output(matched)
        else:
            output += '<h1>File: <a href="%s" target="_blank" rel="nofollow noopener noreferrer">%s</a></h1>'%(escape(url),escape(url))
            for match in matched:
                _matched = match.get('matched')
                _named = match.get('name')
                header = '<div class="text">%s'%(_named.replace('_',' '))
                body = ''
                # find same thing in multiple context
                if match.get('multi_context'):
                    # remove duplicate
                    no_dup = []
                    for context in match.get('context'):
                        if context not in no_dup:
                            body += '</a><div class="container">%s</div></div>'%(context)
                            body = body.replace(
                                context,'<span style="background-color:yellow">%s</span>'%context)
                            no_dup.append(context)
                        # --
                else:
                    body += '</a><div class="container">%s</div></div>'%(match.get('context')[0] if len(match.get('context'))>1 else match.get('context'))
                    body = body.replace(
                        match.get('context')[0] if len(match.get('context')) > 0 else ''.join(match.get('context')),
                        '<span style="background-color:yellow">%s</span>'%(match.get('context') if len(match.get('context'))>1 else match.get('context'))
                    )
                output += header + body
    if args.output != 'cli':
        html_save(output)
