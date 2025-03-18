import re
from header import LogginStatusHeader,UnStatuHeader
from address import URL
from progressbar import ProgressBar, Percentage, Bar
from playwright.async_api import async_playwright
from urllib.parse import quote
from datetime import datetime
import requests,base64,os,json
import ddddocr
import asyncio
import logging
logging.basicConfig(filename='log.log',format='%(asctime)s|%(levelname)s|%(message)s',level=logging.INFO)

class Course:
    '''
    :param userName: str           用户名，通常为手机号
    :param usersPwd:str            账户密码，需要填写加密后的字符串，可以通过浏览器捕捉
    :var credit:dict             个人分数，字典
    :var cookie:dict             登录返回的token字段，字典
    :var compulsoryCredit:float  已获得的必修学分
    :var electivesCredit :float  已获得的选修学分
    :var  year:int                当前年份，自动获取
    :var  finishCredit_c:float    必修学分上限
    :var  finishCredit_e:float    选修学分上限
    :var  courseId:list           所有待学习的课程id
    :var  courseParam:object      可迭代对象，self.feedCourse()实例
    '''
    def __init__(self,userName:str,usersPwd:str,Creditc:float=25,Credite:float=25,headless:bool=True):
        self.page = None
        self.context = None
        self.browser = None
        self.headless = headless
        self.userName = userName
        self.usersPwd = usersPwd    #用户输入密码
        self.credit = {}
        self.cookie = {}
        self.compulsoryCredit = 0.0
        self.electivesCredit = 0.0
        self.year = datetime.now().year
        self.finishCredit_c = Creditc  # 必修学时上限
        self.finishCredit_e = Credite  # 选修学时上限
        self.courseId = []
        self.courseParam = self.feedCourse()
        self.Pwd = None #加密密码字符串
    async def run(self):
        '''入口程序，初始化浏览器驱动，模拟登录，开始学习。'''
        async with async_playwright() as playwright:
            try:
                self.browser = await playwright.chromium.launch(channel='msedge', headless=self.headless, args=['--mute-audio','--start-maximized'])
                self.context = await self.browser.new_context(no_viewport=True)
            except:
                self.browser = await playwright.chromium.launch(channel='chrome', headless=self.headless, args=['--mute-audio','--start-maximized'])
                self.context = await self.browser.new_context(no_viewport=True)
            self.page = await self.context.new_page()
            try:
                await self.login()
                cookie = await self.loadCookie()
                await self.context.add_cookies(cookie)
                self.page = await self.context.new_page()
                status = await self.checkCredit()
                if status:
                    await self.checkCourse()  # 未完成设定学时学分，将检查现有已选课程是否满足完成条件，不够将选课补充（仅限选修课）
                stauts1 = True
                while (status and stauts1):
                    stauts1 = await self.courseLearn()
                    status = await self.checkCredit()
                await self.browser.close()
            except Exception as e:
                await self.browser.close()
                raise ValueError(e)

    async def login(self):
        '''登录函数，检查本地cookie是否存在，存在时加载cookie验证有效性，不存在请求新cookie并登录'''
        isLogin = False     #登录成功标志
        if os.path.exists(f"./{self.userName}_cookies.txt"):
            with open(f"./{self.userName}_cookies.txt") as f:
                self.cookie = json.load(f)
            # 检查cookie有效性
            payload = {"studentId": self.cookie['studentId'], "year": self.year}
            res = requests.post(URL['online']['requestUrl'], json=payload,headers=LogginStatusHeader(cookie=self.cookie, refer=URL['online']['refer']))
            if res.json()['code'] == 0:
                isLogin = True
                self.credit =  res.json()['data']
        if not isLogin:
            await self.getPWD()   #获取加密密码
            codeRespon = requests.get(url=URL['getCode']['requestUrl'], headers=UnStatuHeader).json()
            code = ddddocr.DdddOcr(beta=True,show_ad=False).classification(base64.b64decode(codeRespon['codeImg']))
            login = URL['login']
            pyloader = {"userName": self.userName, "usersPwd": self.Pwd, "verificationCode": code,"verifyCode": codeRespon['uuid']}
            cookie = requests.post(url=login['requestUrl'], json=pyloader, headers=UnStatuHeader)
            if cookie.json()['code'] == 0:
                self.cookie = cookie.json()['data']
                with open(f"./{self.userName}_cookies.txt", 'w') as f:
                    f.write(json.dumps(cookie.json()['data']))
                payloader = {"studentId": self.cookie['studentId'], "year": self.year}
                res = requests.post(URL['online']['requestUrl'], json=payloader,headers=self.header(refer=URL['online']['refer']))
                self.credit =  res.json()['data']
                print('原cookie失效，重新申请cookie。')
                logging.info('原cookie失效，重新申请cookie。')
            else:
                raise ValueError(f"登录出错，{cookie.json()['msg']}")

    async def loadCookie(self):
        '''加载cookie，对cookie数据进行拼接'''
        tmplist = []
        for k, v in self.cookie.items():
            if k == 'token':
                k = 'wlxytk'
            tmplist.append({'name': k, 'value': quote(v), 'domain': '.jxgbwlxy.gov.cn','path':'/'})
        return tmplist

    async def getPWD(self):
            page = await self.context.new_page()
            await page.route('https://study.jxgbwlxy.gov.cn/api/sys/login', self.handle_request)
            await page.goto('https://study.jxgbwlxy.gov.cn/index?redirect=%2Fstudy%2Fdata')
            await page.locator('//*[@id="app"]/div[1]/div[2]/form/div[1]/div/div/input').fill(self.userName)
            await page.locator('//*[@id="app"]/div[1]/div[2]/form/div[2]/div/div/input').fill(self.usersPwd)
            await page.locator('//*[@id="app"]/div[1]/div[2]/form/div[3]/div/div/div/input').fill('test')
            await page.locator('//*[@id="app"]/div[1]/div[2]/div[2]/button').click()
            await page.close()
    async def handle_request(self, route):
        #捕捉login请求中的post_data,获取加密后的密码
        tmpdict = json.loads(route.request.post_data)
        self.Pwd = tmpdict['usersPwd']
        await route.continue_()

    def header(self,refer:str):
        '''拼接请求头'''
        return LogginStatusHeader(cookie=self.cookie, refer=refer)
    async def checkCredit(self):
        '''检查当前用户总学时，分必修和选修，返回参数bool值，不满足学时要求是返回真，否则返回假。并结束学习。'''
        payload = {"studentId": self.cookie['studentId'], "year": self.year}
        res = requests.post(URL['online']['requestUrl'], json=payload,headers=LogginStatusHeader(cookie=self.cookie, refer=URL['online']['refer']))
        self.credit = res.json()['data']
        self.compulsoryCredit = float(self.credit['compulsoryCredit'])
        self.electivesCredit = float(self.credit['electivesCredit'])
        print(f'当前必修分为：{self.compulsoryCredit}；选修分为：{self.electivesCredit}。')
        logging.info(f'当前必修分为：{self.compulsoryCredit}；选修分为：{self.electivesCredit}。')
        if self.compulsoryCredit < self.finishCredit_c or self.electivesCredit < self.finishCredit_e:
            return True
        else:
            print('已满足学时要求，无须继续学习！')
            logging.info('已满足学时要求，无须继续学习！')
            return False
    async def checkCourse(self):
        '''检查当前用户所选课程，未满足学时要求时，将课程加入待看列表，全局参数self.courseId,学习子程序从该参数中读取课程信息，并发送学习请求'''
        if self.compulsoryCredit<self.finishCredit_c:
            # 必修课无法选课，且存在达不到设定限制的可能性
            payloader = {'studentId':self.cookie['studentId'], 'completed': "0", 'size': 8, 'current': 1}
            res = requests.post(URL['annualPortalCourseListNew']['requestUrl'], json=payloader,headers=self.header(refer=URL['annualPortalCourseListNew']['refer']))
            tmp_sum = 0
            for data in res.json()['data']['records']:
                id = data['courseware']['id']
                tmp_sum += data['credit']-data['creditsEarned']
                if id not in self.courseId:
                    self.courseId.append(id)
                if tmp_sum+self.compulsoryCredit >= self.finishCredit_c:
                    break
            if tmp_sum+self.compulsoryCredit < self.finishCredit_c:
                self.finishCredit_c = tmp_sum + self.compulsoryCredit
                print(f'必修课分数{self.finishCredit_c}无法满足预设值，所有课程学习结束后将停止学习，请登录网页核查！')
                logging.info(f'必修课分数{self.finishCredit_c}无法满足预设值，所有课程学习结束后将停止学习，请登录网页核查！')
        if self.electivesCredit<self.finishCredit_e:
            #必修课可以选课
            tmp_electives = self.finishCredit_e - self.electivesCredit
            payloader = {'studentId': self.cookie['studentId'], 'completed': "0", 'size': 8, 'current': 1}
            res = requests.post(URL['myElectivesNew']['requestUrl'], json=payloader,headers=self.header(refer=URL['myElectivesNew']['refer']))
            tmp_sum = 0
            for data in res.json()['data']['records']:
                id = data['courseware']['id']
                tmp_sum += data['credit'] - data['creditsEarned']
                if id not in self.courseId:
                    self.courseId.append(id)
                if tmp_sum+self.electivesCredit >= self.finishCredit_e:
                    print('选修课内容已满足学时要求，即将开始学习！')
                    logging.info('选修课内容已满足学时要求，即将开始学习！')
                    break
            if tmp_sum < tmp_electives:
                print(f'选修分还差{tmp_electives-tmp_sum},开始自动选课。')
                logging.info(f'选修分还差{tmp_electives-tmp_sum},开始自动选课。')
                await self.choiceCourse(tmp_electives-tmp_sum)
        return self.courseId
    async def getCourseById(self,id:str):
        '''通过课程id获取课程请求信息，接收一个参数：课程id'''
        payloader = {'id': id, 'studentId': self.cookie['studentId']}
        res = requests.post(URL['findCoursewareById']['requestUrl'], json=payloader,headers=self.header(refer=URL['findCoursewareById']['refer'])).json()
        result = f"id={res['data']['id']}&mainplatformparentcoursewareId={res['data']['mainplatformparentcoursewareId']}&platformcoursewaretypeId=:{res['data']['platformcoursewaretypeId']}&resourceType={res['data']['resourceType']}&courseStudyType=1"
        return result
    async def feedCourse(self):
        '''课程参数generator，该函数被绑定给全局参数self.courseParam，在学习课程的时候调用__anext__()方法，
        不断获取待学习课程列表中课程的请求参数'''
        for id in self.courseId:
            yield await self.getCourseById(id)
    async def choiceCourse(self,scorce:float):
        '''选课子程序，当已选课程不满足学时要求时，从课程库开始选课，达到学时要求后停止，接收一个参数scorce：所需选课学时'''
        payloader = {'id': None, 'name': "", 'sort': 0, 'studentId': self.cookie['studentId'], 'size': 50, 'current': 1, 'year': "", 'parentId': "0"}
        res = requests.post(URL['courseOverview']['requestUrl'], json=payloader,headers=self.header(refer=URL['courseOverview']['refer'])).json()
        tmp = 0
        for data in res['data']['records']:
            if data['elective'] == '已加选修':
                continue
            data['studentId'] = self.cookie['studentId']
            respon = requests.post(URL['joinIn']['requestUrl'], json=data, headers=self.header(refer=URL['joinIn']['refer'])).json()
            if respon['code'] == 0:
                self.courseId.append(data['id'])
                tmp += float(data['credits'])
            if tmp >= scorce:

                break
    async def courseLearn(self):
        '''课程学习的主程序，通过courseParam.__anext__()方法，调用不同课程的请求参数，拼接后打开新的页面，开始学习'''
        try:
            param = await self.courseParam.__anext__()
            # self.page = await self.context.new_page()
            await self.page.goto(f"https://study.jxgbwlxy.gov.cn/video?{param}")
            await asyncio.sleep(1)
            await self.clickStart()
            await self.page.close()
            return True
        except StopAsyncIteration:
            return False
    async def clickStart(self):
        '''干部网络学院不允许同时打开多个视频学习，甚至短时间内先后打开不同的课程都被判定有多个视频，此时会
        弹出单独的页面，让用户选择要播放的课程。因此需要查找重复播放页面和播放按钮，并点击'''
        try:
            smt = self.page.get_by_text('此次打开的课件：')
            if await smt.count() > 0:
                await self.page.locator('//*[@class="choose-body"]/div[2]/span[2]').click()
            img = self.page.locator('//*[@class="video_cover"]/img')
            if await img.is_visible():
                await img.click()
            await self.clickSubCourse()
        except Exception as e:
            print(e)
            raise ValueError(e)
    async def clickSubCourse(self):
        '''课程下的不同课件切换'''
        await self.page.wait_for_selector('//*[@class="top_tips flex-between-center"]/div[1]')          #等待元素出现
        tmp_totle = await self.page.locator('//*[@class="top_tips flex-between-center"]/div[1]').text_content()
        print('当前所学课程%s'%tmp_totle)
        totle = self.matchInt(tmp_totle)
        for i in range(totle):
            title = await self.page.locator(f'//*[@class="kc_list"]/li[{i+1}]/h5').text_content()
            dulatime_tmp = await self.page.locator(f'//*[@class="kc_list"]/li[{i + 1}]/div/span[1]').text_content() #课程总时长
            curent_tmp = await self.page.locator(f'//*[@class="kc_list"]/li[{i + 1}]/div/span[2]').text_content()   #课程学习进度
            if self.matchInt(curent_tmp) == 100:
                logging.info(f'{title}学习进程100%，跳过！')
                print(f'{title}学习进程100%，跳过！')
                continue
            dulatime = (100-self.matchInt(curent_tmp)) / 100 *self.matchInt(dulatime_tmp)   #根据当前学习进度，计算剩余学习时长
            await self.page.locator(f'//*[@class="kc_list"]/li[{i + 1}]/h5').click()
            print('%s将学习%s分钟' % (title, dulatime))
            logging.info('%s将学习%s分钟' % (title, dulatime))
            pbar = ProgressBar(widgets=[Percentage(),Bar()],maxval=100).start()
            # await asyncio.sleep(dulatime*60+10)
            pbar.update(self.matchInt(curent_tmp))
            click_sum = 0
            while(dulatime):
                await asyncio.sleep(60)
                dulatime -= 1
                pbar.update((1-dulatime/self.matchInt(dulatime_tmp))*100)
                click_sum += 1
                if click_sum == 10:
                    await self.page.locator(f'//*[@class="vb-l"]/button[1]').click()
                    click_sum = 0
            await asyncio.sleep(20)
            await self.page.locator(f'//*[@class="vb-l"]/button[1]').click()
            await asyncio.sleep(1)
    def matchInt(self,s:str):
        pa = re.compile('\d+')
        return int(pa.findall(s)[0])



