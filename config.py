import os,configparser,sys,asyncio,logging
logging.basicConfig(filename='log.log',format='%(asctime)s|%(levelname)s|%(message)s',level=logging.INFO)

async def confighandle(configfile):
    conf = configparser.ConfigParser()
    if os.path.exists(configfile):
        conf.read(configfile,encoding='UTF-8')
        section = 'ACCOUNT'
        sectionParam = 'PARAM'
        try:
            creditc = conf.getfloat(sectionParam,'VALUE1')
            credite = conf.getfloat(sectionParam,'VALUE2')
            headless = conf.getboolean(sectionParam,'VALUE3')
            # print(creditc,credite,headless)
        except:
            creditc = False
        if conf.has_section(section):
            try:
                L = []
                i = 1
                for userName,usersPwd in conf.items(section):
                    L.append([userName,usersPwd])
                    print(f'{i}:{userName}')
                    i += 1
                if len(L) > 1:
                    user = int(input('请选择用户开始学习（输入序号）：'))
                    print(f'已选择用户{L[user-1][0]}，开始学习')
                    logging.info(f'已选择用户{L[user-1][0]}，开始学习')
                else:
                    print(f'将选择当前{L[0][0]}用户,开始学习！')
                    logging.info(f'将选择当前{L[0][0]}用户,开始学习！')
                    user=1
                if creditc:
                    return L[user-1][0],L[user-1][1],creditc,credite,headless
                else:
                    return L[user-1][0],L[user-1][1]
            except Exception as e:
                print('配置文件出错，请检查后重试。')
        else:
            print('配置文件出错，请检查后重试。')
    else:
        raise FileExistsError('config.txt文件未找到，请将配置文件放在主程序同级目录！')


# print(confighandle('config.txt').len())
