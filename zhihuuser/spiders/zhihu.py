# -*- coding: utf-8 -*-
import json

from scrapy import Spider,Request

from zhihuuser.items import UserItem


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_user = 'excited-vczh'

    # 拼接用户信息接口url
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    # 拼接关注接口url
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        # 实现构造用户自己和其关注的人的json的url
        # 请求轮子自己本身的json列表
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        # 请求轮子关注的人的json列表
        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20), callback=self.parse_follows)

    def parse_user(self, response):
        # 将返回的轮子哥的json赋值给item输出
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item

        # 层层递归，根据轮子哥关注的人的url_token获取轮子哥关注的人的关注的人的列表
        yield Request(self.follows_url.format(user=result.get('url_token'), include=self.follows_query, limit=20, offset=0), self.parse_follows)

    def parse_follows(self, response):
        # 将返回的轮子哥关注的人的json输出
        results = json.loads(response.text)
        # 先解析
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query), self.parse_user)
        # 再分页
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_follows)