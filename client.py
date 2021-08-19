import json, requests, datetime, hmac, hashlib

class talkBankClient():
    def __init__(self, baseUrl, partnerId, partnerToken):
        self.baseUrl = baseUrl
        self.partnerId = partnerId
        self.partnerToken = partnerToken

        self.apiDict = {
            "getBalance": "/api/v1/balance",
            "getHistory": "/api/v1/transactions",
            "getPaymentPage": "/api/v1/charge/%CLIENT_ID%/unregistered/card/with/form",
            "getPaymentStatus": "/api/v1/payment/",
            "itelierCreateOrder": "/api/v1/marketplace/itelier/order",
            "itelierCreateAtelier": "/api/v1/marketplace/itelier/atelier"
        }

    def getHashSHA256(self, data):
        m = hashlib.sha256()
        m.update(data.encode())
        return str(m.hexdigest())

    def create_sha256_signature(self, message):
        message = message.encode()
        return hmac.new(self.partnerToken.encode(), message, hashlib.sha256).hexdigest()

    def createAuthorizationField(self, method: str, addUrl: str, body: str):
        method = str(method).upper()
        addUrl = addUrl.split("?")
        if len(addUrl) == 1:
            requestPath = addUrl[0]
            requestQuery = ""
        else:
            requestPath = addUrl[0]
            requestQuery = addUrl[1]

        if requestPath is None:
            return None

        resultList = []
        resultList.append(method)
        resultList.append(requestPath)

        queryString = ""
        if requestQuery != "":
            tempList = requestQuery.split("&")
            tempDict = {}
            for tempArg in tempList:
                pair = tempArg.split("=")
                if len(pair) != 2:
                    return None
                tempDict.update({pair[0]: pair[1]})
            queryList = []
            for i in sorted(tempDict.keys()):
                queryList.append(str(i) + "=" + str(tempDict.get(i)))
            queryString = '&'.join(queryList)
        resultList.append(queryString)

        dateTime = (datetime.datetime.utcnow()).strftime("%a, %d %b %Y %X GMT") #Format: Tue, 19 Feb 2019 08:43:02 GMT
        resultList.append("date:%s" % dateTime)

        hashBody = self.getHashSHA256(body)
        resultList.append("tb-content-sha256:%s" % hashBody)

        resultList.append(hashBody)
        resultString = '\n'.join(resultList)

        signature = self.create_sha256_signature(resultString)
        return ("TB1-HMAC-SHA256 %s:%s" % (self.partnerId, signature), hashBody, dateTime)

    def getBalance(self):
        auth, hashBody, dateTime = self.createAuthorizationField("GET", self.apiDict.get("getBalance"), "")
        response = requests.get(self.baseUrl + self.apiDict.get("getBalance"),
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def getHistory(self):
        auth, hashBody, dateTime = self.createAuthorizationField("GET", self.apiDict.get("getHistory"), "")
        response = requests.get(self.baseUrl + self.apiDict.get("getHistory"),
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def getPaymentPage(self, clientId, amount: int, txID): # amount in 1/100 of Ruble
        body = {"amount": int(amount), "redirect_url": "http://example.com", "order_slug": txID}
        uri = self.apiDict.get("getPaymentPage").replace("%CLIENT_ID%", clientId)
        auth, hashBody, dateTime = self.createAuthorizationField("POST", uri, json.dumps(body))
        response = requests.post(self.baseUrl + uri,
            json=body,
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def getPaymentStatus(self, txID):
        auth, hashBody, dateTime = self.createAuthorizationField("GET", self.apiDict.get("getPaymentStatus") + txID, "")
        response = requests.get(self.baseUrl + self.apiDict.get("getPaymentStatus") + txID,
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def itelierCreateOrder(self, atelierId, atelierName, atelierBranchId, atelierBranchAddress, clientId, clientName, transactionId, transactionDetails):
        data = {
            "atelier_id": atelierId,
            "atelier_name": atelierName,
            "atelier_branch_id": atelierBranchId,
            "atelier_branch_address": atelierBranchAddress,
            "client_id": clientId,
            "client_name": clientName,
            "transaction_id": transactionId,
            "transaction_details": transactionDetails
        }
        uri = self.apiDict.get("itelierCreateOrder")
        auth, hashBody, dateTime = self.createAuthorizationField("POST", uri, json.dumps(data))
        response = requests.post(self.baseUrl + uri,
            json=data,
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def itelierCreateAtelier(self, atelierId, atelierName, atelierDetails):
        data = {
            "atelier_id": atelierId,
            "atelier_name": atelierName,
            "atelier_details": atelierDetails
        }
        uri = self.apiDict.get("itelierCreateAtelier")
        auth, hashBody, dateTime = self.createAuthorizationField("POST", uri, json.dumps(data))
        response = requests.post(self.baseUrl + uri,
            json=data,
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()