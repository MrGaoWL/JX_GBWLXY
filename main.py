import sys
from learn import Course
from config import confighandle
import asyncio,os,sys
import logging
logging.basicConfig(filename='log.log',format='%(asctime)s|%(levelname)s|%(message)s',level=logging.INFO)



async def main():
    try:
        tmp = await confighandle(f'./config.txt')
        try:
            userName, usersPwd, Creditc, Credite, headless = tmp
        except:
            userName, usersPwd = tmp
        c = Course(userName, usersPwd, Creditc, Credite, headless)
        await c.run()
    except Exception as e:
        print(f'发生错误：{e}\n界面将在10秒后关闭，请检查后重新运行程序。')
        logging.error(e)
        await asyncio.sleep(10)

    # tmp = await confighandle(f'./config.txt')
    # try:
    #     userName, usersPwd, Creditc, Credite, headless = tmp
    # except:
    #     userName, usersPwd = tmp
    # c = Course(userName, usersPwd, Creditc, Credite, headless)
    # await c.run()



if __name__ == "__main__":
    asyncio.run(main())
