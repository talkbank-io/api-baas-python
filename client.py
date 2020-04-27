import json, requests, datetime
import hmac, hashlib, uuid

class talkBankGate():
    def __init__(self):
        self.baseUrl = "https://baas.talkbank.io"

        self.clientID = "CLIENT_ID"
        self.partnerID = "P_ID"
        self.partnerToken = "P_TOKEN"

        self.apiDict = {
            "testPost": "/api/v1/method",
            "getBalance": "/api/v1/balance",
            "getHistory": "/api/v1/transactions",
            "createNewClient": "/api/v1/clients",
            "getPaymentPage": "/api/v1/charge/" + self.clientID + "/unregistered/card/with/form"
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
        addUrl = addUrl.split("?") # разделяю URL и аргументы
        if len(addUrl) == 1:
            requestPath = addUrl[0]
            requestQuery = ""
        else:
            requestPath = addUrl[0]
            requestQuery = addUrl[1]

        if requestPath is None: # если УРЛ пустой
            return None

        resultList = [] # массив элементов для сбора строки для подписи
        resultList.append(method) # добавляю метов в апперкейсе
        resultList.append(requestPath) # добавляю УРЛ

        # сортирую строку аргументов УРЛа по имени аргумента и скливаю обратно в строку
        queryString = ""
        if requestQuery != "":
            tempList = requestQuery.split("&")
            tempDict = {}

            for tempArg in tempList:
                pair = tempArg.split("=")
                if len(pair) != 2:
                    print("argumets error!")
                    return None
                tempDict.update({pair[0]: pair[1]})

            queryList = []
            for i in sorted(tempDict.keys()):
                queryList.append(str(i) + "=" + str(tempDict.get(i)))
            queryString = '&'.join(queryList)
        resultList.append(queryString) # добавляю отсортированную строку аргументов


        dateTime = (datetime.datetime.utcnow()).strftime("%a, %d %b %Y %X GMT") #Tue, 19 Feb 2019 08:43:02 GMT
        resultList.append("date:%s" % dateTime) # формирую текущую дату и время -3 часа

        hashBody = self.getHashSHA256(body) # беру Хэш тела параметров
        print(body, " --HASH_SHA256-->", hashBody)
        resultList.append("tb-content-sha256:%s" % hashBody) # добавляю Хэш тела с префиксом

        resultList.append(hashBody) # добавляю хэш тела в голом виде
        resultString = '\n'.join(resultList) # склеиваю массив через /n

        signature = self.create_sha256_signature(resultString) # подписываю строку
        print(resultString)
        print("--HMAC_SHA256-->", signature)
        return ("TB1-HMAC-SHA256 %s:%s" % (self.partnerID, signature), hashBody, dateTime)

    def _getBalance(self): # work
        auth, hashBody, dateTime = self.createAuthorizationField("GET", self.apiDict.get("getBalance"), "")
        response = requests.get(self.baseUrl + self.apiDict.get("getBalance"),
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def _getHistory(self): # work
        auth, hashBody, dateTime = self.createAuthorizationField("GET", self.apiDict.get("getHistory") + "", "")
        response = requests.get(self.baseUrl + self.apiDict.get("getHistory"),
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()

    def _createNewClient(self): # NOT work
        body = {
            "client_id":"19633063",
            "person":{
                "phone":"9687865888",
            }
        }
        auth, hashBody, dateTime = self.createAuthorizationField("POST", self.apiDict.get("createNewClient") + "", json.dumps(body))
        response = requests.post(self.baseUrl + self.apiDict.get("createNewClient"),
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        print({'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth})
        return response.json()

    def _getPaymentPage(self, amount: int, txID): # NOT work
        body = {"amount": int(amount*1000), "redirect_url": "http://google.com", "order_slug":txID}
        print(self.baseUrl + self.apiDict.get("getPaymentPage"))
        auth, hashBody, dateTime = self.createAuthorizationField("POST", self.apiDict.get("getPaymentPage") + "", json.dumps(body))
        response = requests.post(self.baseUrl + self.apiDict.get("getPaymentPage"),
            json=body,
            headers={'Content-Type': 'application/json', 'TB-Content-SHA256': hashBody, 'Date': dateTime, 'Authorization': auth}
        )
        return response.json()


    ### PUBLIC

    def getPaymentUrl(self, amount):
        txID = uuid.uuid4()
        json = self._getPaymentPage(amount, str(txID))
        if json is None:
            return None

        url = json.get("charge_link")
        if url is None:
            return "http://www.google.com"
        else:
            return url
