# -*-coding:utf-8 -*-
import json,datetime,time

import base64
import hashlib
import hmac
import json
import os
import time
import requests
import datetime
lfasr_host = 'http://raasr.xfyun.cn/api'

# 请求的接口名
api_prepare = '/prepare'
api_upload = '/upload'
api_merge = '/merge'
api_get_progress = '/getProgress'
api_get_result = '/getResult'
# 文件分片大下52k
file_piece_sice = 10485760

# ——————————————————转写可配置参数————————————————
# 转写类型
lfasr_type = 0
# 是否开启分词
has_participle = 'false'
has_seperate = 'true'
# 多候选词个数
max_alternatives = 0
# 子用户标识
suid = ''

#"""slice id生成器"""
class SliceIdGenerator:
    def __init__(self):
        self.__ch = 'aaaaaaaaa`'

    def getNextSliceId(self):
        ch = self.__ch
        j = len(ch) - 1
        while j >= 0:
            cj = ch[j]
            if cj != 'z':
                ch = ch[:j] + chr(ord(cj) + 1) + ch[j + 1:]
                break
            else:
                ch = ch[:j] + 'a' + ch[j + 1:]
                j = j - 1
        self.__ch = ch
        return self.__ch

appid="***"
secret_key="*****"

def start(upload_file_path,taskid_re=False):
    def gene_params(apiname, taskid=None, slice_id=None):
        ts = str(int(time.time()))
        m2 = hashlib.md5()
        m2.update((appid + ts).encode('utf-8'))
        md5 = m2.hexdigest()
        # md5 = bytes(md5, encoding='utf-8')
        md5 = bytes(md5)
        # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
        signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        # signa = str(signa, 'utf-8')
        signa = str(signa)
        if not taskid_re:
            file_len = os.path.getsize(upload_file_path)
            file_name = os.path.basename(upload_file_path)
        else:
            file_len=100
            file_name='get_result'
        param_dict = {}

        if apiname == api_prepare:
            # slice_num是指分片数量，如果您使用的音频都是较短音频也可以不分片，直接将slice_num指定为1即可
            slice_num = int(file_len / file_piece_sice) + (0 if (file_len % file_piece_sice == 0) else 1)
            param_dict['app_id'] = appid
            param_dict['signa'] = signa
            param_dict['ts'] = ts
            param_dict['file_len'] = str(file_len)
            param_dict['file_name'] = file_name
            param_dict['slice_num'] = str(slice_num)
        elif apiname == api_upload:
            param_dict['app_id'] = appid
            param_dict['signa'] = signa
            param_dict['ts'] = ts
            param_dict['task_id'] = taskid
            param_dict['slice_id'] = slice_id
        elif apiname == api_merge:
            param_dict['app_id'] = appid
            param_dict['signa'] = signa
            param_dict['ts'] = ts
            param_dict['task_id'] = taskid
            param_dict['file_name'] = file_name
        elif apiname == api_get_progress or apiname == api_get_result:
            param_dict['app_id'] = appid
            param_dict['signa'] = signa
            param_dict['ts'] = ts
            param_dict['task_id'] = taskid
        return param_dict

    # 请求和结果解析，结果中各个字段的含义可参考：https://doc.xfyun.cn/rest_api/%E8%AF%AD%E9%9F%B3%E8%BD%AC%E5%86%99.html
    def gene_request(apiname, data, files=None, headers=None):
        response = requests.post(lfasr_host + apiname, data=data, files=files, headers=headers)
        result = json.loads(response.text)
        if result["ok"] == 0:
            print("{} success:".format(apiname) + str(result))
            return result
        else:
            print("{} error:".format(apiname) + str(result))
            exit(0)
            return result

    # 预处理
    def prepare_request():
        return gene_request(apiname=api_prepare,
                                 data=gene_params(api_prepare, taskid=None, slice_id=None))

    # 上传
    def upload_request(taskid, upload_file_path):
        file_object = open(upload_file_path, 'rb')
        yield 'uploading file...plz wait DONT CLOSE YOUR BROWSER!!'
        try:
            index = 1
            sig = SliceIdGenerator()
            while True:
                yield 'uploading slice %s ' % str(index)
                content = file_object.read(file_piece_sice)
                if not content or len(content) == 0:
                    break
                files = {
                    "filename": gene_params(api_upload).get("slice_id"),
                    "content": content
                }
                response = gene_request(api_upload,
                                             data=gene_params(api_upload, taskid=taskid,
                                                                   slice_id=sig.getNextSliceId()),
                                             files=files)
                if response.get('ok') != 0:
                    # 上传分片失败
                    yield ('upload slice fail, response: ' + str(response))
                    # return False
                yield ('upload slice ' + str(index) + ' success')
                index += 1
        finally:
            'file index:' + str(file_object.tell())
            file_object.close()
        # return True


    # 合并
    def merge_request(taskid):
        return gene_request(api_merge, data=gene_params(api_merge, taskid=taskid))

    # 获取进度
    def get_progress_request(taskid):
        return gene_request(api_get_progress, data=gene_params(api_get_progress, taskid=taskid))

    # 获取结果
    def get_result_request(taskid):
        return gene_request(api_get_result, data=gene_params(api_get_result, taskid=taskid))

    if not taskid_re:
        yield '<h3>1. 预处理，请勿关闭或刷新浏览器</h3> '
        pre_result = prepare_request()
        from mutagen import mp3,mp4
        if 'mp3' in upload_file_path[-5:]:
            audio = mp3.MP3(upload_file_path)
            audiolength=audio.info.length
            yield 'filelength: '+str(audio.info.length)+' seconds'
        if 'm4a' in upload_file_path[-5:]:
            audio=mp4.MP4(upload_file_path)
            audiolength = audio.info.length
            yield 'filelength: '+str(audio.info.length)+' seconds'

        speed=15
        totaltime=float(speed*(float(audiolength)/60)/60)
        if totaltime == 0:totaltime = 1
        yield '预计完成时间: '+str(totaltime)+'分钟'

        taskid = pre_result["data"]
        yield '<h3> 2 . 分片上传至服务器，请耐心等待...预计需要：'+str(float(audiolength/10))+'秒</h3> '
        for msg in upload_request(taskid=taskid, upload_file_path=upload_file_path):
            yield msg
        yield '<h3> 3 . 文件合并</h3>'
        merge_request(taskid=taskid)
        yield '<h3> 4 . 获取任务进度 （每10秒刷新一次），taskid: %s </h3>' % str(taskid)
        def completed_per(pasttime):
            per=pasttime/(totaltime*60)*100
            if per > 99:
                per = 99.99999
            return str(per)+'%'

        pasttime=0
        while True:
            # 每隔10秒获取一次任务进度
            pasttime=pasttime+10
            progress = get_progress_request(taskid)
            progress_dic = progress
            if progress_dic['err_no'] != 0 and progress_dic['err_no'] != 26605:
                print('task error: ' + progress_dic['failed'])
                return
            else:
                data = progress_dic['data']
                task_status = json.loads(data)
                if task_status['status'] == 9:
                    # print ('task ' +taskid + ' finished')
                    break
                yield ('The task is in processing, task status: ' + data+'  completed: %s' % completed_per(pasttime))

            # yield '# 每次获取进度间隔10S'
            time.sleep(10)

        yield '<h3> 5 . 完成转写</h3>'
        yield get_result_request(taskid=taskid)
    else:
        yield get_result_request(taskid=taskid_re)
