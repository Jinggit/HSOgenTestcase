# -*- coding: utf-8 -*-
import json
import re
import os
from gen_pairwise_test.ptg import *
import ast
import urllib
import codecs

class genTestcase:
    
    def get_request_content(self,fp):
        '''打开charles抓到的har包，将数据加载成json'''
        f = codecs.open(fp,'r','utf-8')
        content = f.readlines()
        return json.loads(content[0])
    
    def get_uri_argument_from_request(self,req_json):
        '''获取har文件中的全部请求uri以及每个请求uri对应的参数，和请求的类型
        {url1:[['param1','param2'],'POST'], ...}
        '''
        req_dict={}
        for r in req_json['log']['entries']:
            url=r['request']['url']
            url=urllib.unquote(url.encode("utf-8"))
            #print url
            method=r['request']['method']
            params=[]
            #不处理url中包含以下扩展名的的请求
            files_ext = [".js",".css",".cjs",".png",".html",".gif",".jpg",".baidu",".google",".net",".swf",".ico"]
            if all(st not in url for st in files_ext):
                try:
                    if (method == "POST"):
                        pbody=r['request']['postData']['text']
                        p = json.loads(pbody)                
#                         for k in p.keys():
#                             if p[k] == '':
#                                 params.append({k:"${EMPTY}"})
#                             else:
#                                 params.append({k:p[k]})
                        req_dict[url]=[[p],"POST"] 
                        #print req_dict[url][0]
                    else:
                        get_param_string=url.split("?")[-1]
                        url_without_parama=url.split("?")[0]
                        #get_param_list=re.findall('&(.*?)=','&'+get_param_string)
                        #print get_param_string
                        get_param_list=get_param_string.split('&')
                        #print get_param_list
                        get_param_list_list=[l.split('=') for l in get_param_list]
                        #print get_param_list_list
                        get_param_dict_list=[{l[0]:l[1]} for l in get_param_list_list]
                        req_dict[url_without_parama+'?']=[get_param_dict_list,"GET"]
                except:
                    continue
        return req_dict
    
    def gen_common_resource_head(self,req_dict,version,tofile,head_flag="new"):
        root_urls=[]
        for key in req_dict:
            try:
                root=key.split("/")[2]
                root_urls.append(root)
            except:
                continue
        tf=open(tofile,"a")
        #如果head_flag等于append，则按新生文件对待，只会追加api变量记录到已有文件中
        if (head_flag!="append"):
            tf.write("*** Settings ***\n")
            tf.write("Documentation     全局变量\n")
            tf.write("\n")
            tf.write("*** Variables ***\n")
        for root_url in set(root_urls):
            prefix_root_url=root_url.split(".")[0]
            tf.write("${"+prefix_root_url.upper()+"_API_ROOT_URL}    "+"https://"+root_url+"\n")
            #tf.write("${API_ROOT_URL}    "+root_url+"\n")
        tf.write("${API_VERSION}    "+version+"    # API版本号\n")
        tf.write("${USER_AGENT}     iOS/8.400000;iPhone 6 (A1549/A1586);beast/2.2.0.4711\n")
        tf.write("${DEVICE_TOKEN}    04A7DEB91E8C4610B17A638E2EF05CEB\n")
        tf.write("${CONTENT_TYPE}    application/json\n")
        tf.write("${AUTO_USERNAME}    15311446193\n")
        tf.write("${AUTO_PASSWORD}    123456\n")
        tf.write("${SESSION}    ${EMPTY}\n")
        tf.close()
    
    def gen_uri_as_variable_in_common_resource(self,url,method,spliter,uri_prefix,version,tofile):
        tf=open(tofile,"a")
        if url!="method":
            if (method=="POST"):
                uri=url.split(spliter,1)[-1]
                variable_name=uri.split('/')[-1]
                variable_name_upper=variable_name.upper()
                if version in uri:
                    uri=uri.replace(version,"${API_VERSION}")
                tf.write("${"+variable_name_upper+"_URI}    "+uri_prefix+uri+"\n")
            else:
                uri=url.split(spliter)[-1]
                try:
                    variable_name_full=uri.split('?')[-2]
                    variable_name=variable_name_full.split('/')[-1]
                    variable_name_upper=variable_name.upper()
                    if version in uri:
                        variable_name_full=variable_name_full.replace(version,"${API_VERSION}")
                    tf.write("${"+variable_name_upper+"_URI}    "+uri_prefix+variable_name_full+"\n")
                except:
                    uri=url.split(spliter)[-1]
                    variable_name=uri.split('/')[-1]
                    variable_name_upper=variable_name.upper()
                    if version in uri:
                        uri=uri.replace(version,"${API_VERSION}")
                    tf.write("${"+variable_name_upper+"_URI}    "+uri_prefix+uri+"\n")
        tf.close()
    
    def gen_api_resource_head(self,tofile,head_flag="new"):
        tf=open(tofile,"a")
        if (head_flag!="append"):
            tf.write("*** Settings ***\n")
            tf.write("Resource          public_api_resource.txt\n")
            tf.write("\n")
            tf.write("*** Keywords ***\n")
        tf.close()
        
    def gen_api_resource(self,req_dict,spliter,tofile):
        tf=open(tofile,"a")
        for url in req_dict:
            root_url=url.split("/")[2]
            uri=url.split(spliter)[-1]
            if not '?' in uri:
                variable_name=uri.split('/')[-1]
            else:
                variable_name=uri.split('/')[-1]
                variable_name=variable_name.split('?')[-2]
            variable_name_upper=variable_name.upper()
            api_resource_name = variable_name.capitalize()+'_'+req_dict[url][1].lower()
            tf.write(api_resource_name +"\n")
            if (req_dict[url][1]=="POST"):
                param_disc = '    '+"[Arguments]"+'    '+"${session}" +'    ${postbody}'
            else:
                if not 'login' in uri:
                    param_disc='    '+"[Arguments]"+'    '+"${session}"
                else:
                    param_disc='    '+"[Arguments]"+'    '  
                for param in req_dict[url][0]:
                    #print param
                    param_disc = param_disc+'    '+"${"+param.keys()[0]+"}"
            tf.write(param_disc+"\n")
            param_post_disc=''
            if (req_dict[url][1]=="POST"):
                param_post_disc = '    ${postbody}'
            else:
                for param in req_dict[url][0]:
                    param_post_disc = param_post_disc+'    '+param.keys()[0]+'    '+"${"+param.keys()[0]+"}"
            if (req_dict[url][1]=="POST"):
                if 'login' in uri:
                    method="Post Request WIth JSON"
                else:
                    method="Post Request WIth JSON and Token"
            else:
                method="Get Request Pro"
            prefix_root_url=root_url.split(".")[0]
            if not 'login' in uri:
                tf.write("    ${resp}=    "+ method +"    ${"+prefix_root_url.upper()+"_API_ROOT_URL}    ${"+variable_name_upper+"_URI}"+"    ${session}" + param_post_disc+"\n")
                tf.write("    ${status}    ${code}=    Run Keyword And Ignore Error    Set Variable    ${resp.json()['code']}\n")
                tf.write("    ${status}    ${message}=    Run Keyword And Ignore Error    Set Variable    ${resp.json()['message']}\n")
                tf.write("    [Return]    ${resp}    ${code}    ${message}\n")
            else:
                tf.write("    ${resp}=    "+ method +"    ${"+prefix_root_url.upper()+"_API_ROOT_URL}    ${"+variable_name_upper+"_URI}"+"    " + param_post_disc+"\n")
                tf.write("    ${status}    ${code}=    Run Keyword And Ignore Error    Set Variable    ${resp.json()['code']}\n")
                tf.write("    ${status}    ${message}=    Run Keyword And Ignore Error    Set Variable    ${resp.json()['message']}\n")
                tf.write("    ${userToken}=    Run Keyword And Ignore Error    Set Variable    ${resp.json()['value']['userToken']}\n")
                tf.write("    [Return]    ${resp}    ${code}    ${message}    ${userToken}\n")
        tf.close()
    
    def gen_testsuite(self,url,spliter,req_dict,testcase_directory):
        uri=url.split(spliter)[-1]
        if not '?' in uri:
            variable_name=uri.split('/')[-1]
        else:
            variable_name=uri.split('/')[-1]
            variable_name=variable_name.split('?')[-2]
        variable_name_cap=variable_name.capitalize()
        tf=open(testcase_directory+"/"+variable_name_cap+"_"+req_dict[url][1].upper()+".txt","a")
        tf.write("*** Settings ***"+"\n")
        tf.write("Documentation    "+url+"\n")
        tf.write("Force Tags    prod\n")
        tf.write("Resource    all_api_resource.txt\n")
        tf.write("\n")
        tf.close()

    def gen_testcase(self,url,spliter,req_dict,testcase_directory):
        uri=url.split(spliter)[-1]
        if not '?' in uri:
            variable_name=uri.split('/')[-1]
        else:
            variable_name=uri.split('/')[-1]
            variable_name=variable_name.split('?')[-2]
        variable_name_cap=variable_name.capitalize()+"_"+req_dict[url][1].lower()
        value_disc=""
        #print req_dict[url][0]
        if (req_dict[url][1]=="POST"):
            value_disc = '    '+str(req_dict[url][0][0])
        else:
            #print req_dict[url][0]
            for param in req_dict[url][0]:
                value_disc = value_disc+'    '+str(param.values()[0]).decode('UTF-8')
        tf=open(testcase_directory+"/"+variable_name_cap+".txt","a")
        tf.write("*** Test Cases ***"+"\n")
        tf.write(variable_name_cap+"\n")
        tf.write("    [Documentation]    "+url+"\n")
        tf.write("    [Template]    "+variable_name_cap+"_Temp\n")
        if 'login' in uri:
            tf.write("    TestData01: 登录用户    0    成功    ${AUTO_USERNAME}    ${AUTO_PASSWORD}"+"\n")
        else:
            tf.write("    TestData01: 登录用户    0    成功    ${AUTO_USERNAME}    ${AUTO_PASSWORD}"+value_disc.encode('utf8')+"\n")
        tf.write("\n")
        tf.close()
    
    def gen_template_negative(self,req_dict,url,spliter,testcase_directory):
        uri=url.split(spliter)[-1]
        if not '?' in uri:
            variable_name=uri.split('/')[-1]
        else:
            variable_name=uri.split('/')[-1]
            variable_name=variable_name.split('?')[-2]
        variable_name_cap=variable_name.capitalize()+'_'+req_dict[url][1].lower()
        param_disc=""
        #print req_dict[url][0]
        if (req_dict[url][1]=="POST"):
            param_disc = '    ${postbody}'
        else:
            for param in req_dict[url][0]:
                #print param
                param_disc = param_disc+'    '+"${"+param.keys()[0]+"}"
        tf=open(testcase_directory+"/"+variable_name_cap+".txt","a")
        #tf.write("*** Keywords ***"+"\n")
        tf.write(variable_name_cap+"_negative_Temp\n")
        if 'login' in uri:
            tf.write("    [Arguments]    ${testdata_info}    ${code}    ${message}"+param_disc+"\n")
            tf.write("    Log    ${testdata_info}\n")
            tf.write("    ${resp}=    "+variable_name_cap+"    "+param_disc+"\n")
            tf.write("    Should Not Be Equal As Strings    ${resp[1]}    ${code}\n")
            tf.write("    Should Not Be Equal As Strings    ${resp[2]}    ${message}\n")
        else:
            tf.write("    [Arguments]    ${testdata_info}    ${code}    ${message}    ${username}    ${password}"+param_disc+"\n")
            tf.write("    Log    ${testdata_info}\n")
            #tf.write("    ${resp}=    Login    ${username}    ${password}\n")
            tf.write("    ${resp}=    "+variable_name_cap+"    ${SESSION}"+param_disc+"\n")
            tf.write("    Should Not Be Equal As Strings    ${resp[1]}    ${code}\n")
            tf.write("    Should Not Be Equal As Strings    ${resp[2]}    ${message}\n")            
        tf.close()
    
    def gen_testcase_negative(self,url,spliter,req_dict,testcase_directory):
        uri=url.split(spliter)[-1]
        if not '?' in uri:
            variable_name=uri.split('/')[-1]
        else:
            variable_name=uri.split('/')[-1]
            variable_name=variable_name.split('?')[-2]
        variable_name_cap=variable_name.capitalize()+"_"+req_dict[url][1].lower()
        param_list=[]
        #print req_dict[url][0]
        for param in req_dict[url][0]:
            param_list.append(param.keys()[0])
        tf=open(testcase_directory+"/"+variable_name_cap+".txt","a")
        #tf.write("*** Test Cases ***"+"\n")
        tf.write(variable_name_cap+"_negative\n")
        tf.write("    [Documentation]    "+url+"\n")
        tf.write("    [Tags]    notready"+"\n")
        tf.write("    [Template]    "+variable_name_cap+"_negative_Temp\n")
        gp = genPairwisetestdata()
        test_data_list = gp.main('./input_file_temp.txt',param_list)
        count = 0
        for test_data in test_data_list:
            count+=1
            if (req_dict[url][1]=="POST"):
                testdatastr = '    '+str(dict(zip(param_list, test_data)))
            else:
                testdatastr = "    ".join(test_data)
            if 'login' in uri:
                tf.write("    TestData"+str(count)+": 输入组合测试    0    成功    "+testdatastr.encode('utf8')+"\n")
            else:
                tf.write("    TestData"+str(count)+": 输入组合测试    0    成功    ${AUTO_USERNAME}    ${AUTO_PASSWORD}    "+testdatastr.encode('utf8')+"\n")
        tf.write("\n")
        tf.close()
    
    def gen_template(self,req_dict,url,spliter,testcase_directory):
        uri=url.split(spliter)[-1]
        if not '?' in uri:
            variable_name=uri.split('/')[-1]
        else:
            variable_name=uri.split('/')[-1]
            variable_name=variable_name.split('?')[-2]
        variable_name_cap=variable_name.capitalize()+'_'+req_dict[url][1].lower()
        param_disc=""
        #print req_dict[url][0]
        if (req_dict[url][1]=="POST"):
            param_disc = '    ${postbody}'
        else:
            for param in req_dict[url][0]:
                #print param
                param_disc = param_disc+'    '+"${"+param.keys()[0]+"}"
        tf=open(testcase_directory+"/"+variable_name_cap+".txt","a")
        tf.write("*** Keywords ***"+"\n")
        tf.write(variable_name_cap+"_Temp\n")
        if 'login' in uri:
            tf.write("    [Arguments]    ${testdata_info}    ${code}    ${message}"+param_disc+"\n")
            tf.write("    Log    ${testdata_info}\n")
            tf.write("    ${resp}=    "+variable_name_cap+"    "+param_disc+"\n")
            tf.write("    Should Be Equal As Strings    ${resp[1]}    ${code}\n")
            tf.write("    Should Be Equal As Strings    ${resp[2]}    ${message}\n")
        else:
            tf.write("    [Arguments]    ${testdata_info}    ${code}    ${message}    ${username}    ${password}"+param_disc+"\n")
            tf.write("    Log    ${testdata_info}\n")
            #tf.write("    ${resp}=    Login    ${username}    ${password}\n")
            tf.write("    ${resp}=    "+variable_name_cap+"    ${SESSION}"+param_disc+"\n")
            tf.write("    Should Be Equal As Strings    ${resp[1]}    ${code}\n")
            tf.write("    Should Be Equal As Strings    ${resp[2]}    ${message}\n")            
        tf.close()
        
    def gen_all_resource(self,tofile,head_flag="new"):
        tf=open(tofile,"a")
        if (head_flag!="append"):
            tf.write("*** Settings ***\n")
            tf.write("Resource          others_api_resource.txt")
        tf.close()
    
    def gen_public_resource(self,tofile,head_flag="new"):
        tf=open(tofile,"a")
        if (head_flag!="append"):
            tf.write("*** Settings ***\n")
            tf.write("Resource          common_resource.txt")
        tf.close()
    
    def gen_input_file_temp(self,testcase_directory,harfile):
        #如果目录不存在则创建存放测试用例的目录
        if not os.path.exists(testcase_directory):
            os.makedirs(testcase_directory)
        #解析charles抓包文件生成字典
        req_json = gt.get_request_content(harfile)
        req_dict = gt.get_uri_argument_from_request(req_json)
        tf=codecs.open("input_file_temp.txt","w","utf8")
        for key in req_dict:
            for testdata in req_dict[key][0]:
                try:
                    tf.write(testdata.keys()[0].encode('utf8')+':'+testdata.values()[0].encode('utf8')+'\n')
                except Exception as e:
                    print e
                    print testdata
                    continue
        tf.close()
        
    def main(self,testcase_directory,harfile,app_version="v1.0",spliter=".com/"):
        #如果目录不存在则创建存放测试用例的目录
        if not os.path.exists(testcase_directory):
            os.makedirs(testcase_directory)
        #解析charles抓包文件生成字典
        req_json = gt.get_request_content(harfile)
        req_dict = gt.get_uri_argument_from_request(req_json)
        #产生common_resource文件中的头
        gt.gen_common_resource_head(req_dict,app_version,testcase_directory+"/common_resource.txt")
        for key in req_dict:
            #产生common_resource文件中的变量
            gt.gen_uri_as_variable_in_common_resource(key,req_dict[key][1],spliter,"/",app_version,testcase_directory+"/common_resource.txt")
            #产生testsuite
            gt.gen_testsuite(key,spliter,req_dict,testcase_directory)
            #产生happypath testcase
            gt.gen_testcase(key,spliter,req_dict,testcase_directory)
            #产生negative testcase
            gt.gen_testcase_negative(key,spliter,req_dict,testcase_directory)
            #产生template
            gt.gen_template(req_dict,key,spliter,testcase_directory)
            #产生negative template
            gt.gen_template_negative(req_dict,key,spliter,testcase_directory)
        #产生others_api_resource文件头
        gt.gen_api_resource_head(testcase_directory+"/others_api_resource.txt")
        #产生others_api_resource文件，存放api对应的keyword
        gt.gen_api_resource(req_dict,spliter,testcase_directory+"/others_api_resource.txt")
        #产生all_api_resource文件
        gt.gen_all_resource(testcase_directory+"/all_api_resource.txt")
        #gt.gen_public_resource(testcase_directory+"/public_api_resource.txt")
    
if __name__ == "__main__":
    gt = genTestcase()
    gt.main("hso","web_api.har",spliter=".com/")
    #gt.gen_input_file_temp("gx","web_api.har")
