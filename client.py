import json, requests, datetime, hmac, hashlib

class talkBankGate():
    def __init__(self):
        self.baseUrl = "https://baas-staging.talkbank.io" # test server
        #self.baseUrl = "https://baas.talkbank.io" # battle server

        self.clientID = "CLIENT_ID"
        self.partnerID = "PARTNER_ID"
        self.partnerToken = "PARTNER_TOKEN"

        self.apiDict = {
            "getBalance": "/api/v1/balance",
            "getHistory": "/api/v1/transactions",
            "getPaymentPage": "/api/v1/charge/" + self.clientID + "/unregistered/card/with/form",
            "getPaymentStatus": "/api/v1/payment/"
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
        return ("TB1-HMAC-SHA256 %s:%s" % (self.partnerID, signature), hashBody, dateTime)

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

    def getPaymentPage(self, amount: int, txID): # amount in 1/100 of Ruble
        body = {"amount": int(amount), "redirect_url": "http://example.com", "order_slug": txID}
        print(self.baseUrl + self.apiDict.get("getPaymentPage"))
        auth, hashBody, dateTime = self.createAuthorizationField("POST", self.apiDict.get("getPaymentPage"), json.dumps(body))
        response = requests.post(self.baseUrl + self.apiDict.get("getPaymentPage"),
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

if __name__ == '__main__':
    tbg = talkBankGate()
    print(tbg.getBalance())
    print(tbg.getPaymentPage(100, "uniqueTransactionIdForSearch")) # ID can using once!
    print(tbg.getPaymentStatus("uniqueTransactionIdForSearch"))
